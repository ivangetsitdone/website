# Eight seconds of 502

**2026-09-20 · deploy**

We gave a small site a real deploy pipeline. Proving the pipeline worked uncovered three
separate defects in how the site had been deploying all along — and not one of them was the
kind of thing a test suite notices, because all three live in the gap between *the build
succeeded* and *the site is serving*.

This is what that looked like, in order, including the parts where we were wrong.

## Setup: the machine

The site is a contractor's brochure: six pages, a photo archive, and a phone number. The
job of the whole thing is to make someone call.

- **FastAPI + Jinja2**, server-rendered. One route renders every page from a dict.
- **HTMX `hx-boost`** for navigation, which swaps the `<body>` and leaves the `<head>` alone.
- **Vite** bundles the frontend into two files at build time.
- **Caddy** terminates TLS and reverse-proxies to the app. Certificates are automatic.
- **Docker Compose**, two containers, on one 2 GB droplet.
- A three-stage Dockerfile: Node builds assets, Pillow generates 75 images from 35 tracked
  originals, and a Python runtime image carries neither toolchain.

The constraint that shapes everything: one droplet, one maintainer, no ops team, and a
deliberate decision that **the repository is the only artefact**. No registry. The droplet
holds a clone and builds from it.

Deploying meant opening SSH and typing three commands. That works right up until it is done
at the wrong moment, in the wrong directory, or on the wrong host — all of which had already
happened at least once.

## Buildup: merge to live

The first version was about as small as a pipeline gets. On a push to `main`, GitHub Actions
opens one SSH session:

```sh
cd /srv/website
git fetch --prune origin main
git reset --hard "$sha"          # a deploy target, not a workspace
docker compose up -d --build
```

Then it waits for the app container's healthcheck, and two follow-on jobs run the existing
test suites against the live site.

Two repository secrets are the entire trust model: `DEPLOY_KEY`, whose public half is in the
droplet's `authorized_keys`, and `DEPLOY_KNOWN_HOSTS`, which pins the droplet's host key so
the runner cannot be talked into deploying somewhere else.

It worked on the first try. The second run went red.

### The first surprise: a race no laptop could lose

A browser test asserted that after a boosted navigation, `<meta name="description">` matched
the new page. It failed on the runner, twice, on both desktop and mobile — and passed on the
development host every time, including with the CPU throttled 6×.

Reading htmx's source settles it. During a swap it fires `htmx:afterSwap`, *then* sets
`<title>`, *then* waits out a 20ms settle delay before firing `htmx:load`. Our head-sync
ran on `htmx:load`. The test synchronised on the title. So the assertion was reading a
value that was still 20ms in the future, and on a slower machine it lost. Both failures
came on the navigation away from the image-heavy gallery page, which is suggestive —
decoding 35 thumbnails competing with a 20ms timer — but that part is a hypothesis we never
confirmed, and did not need to.

Rather than guess, we instrumented it. A probe that reads the head at `htmx:afterSwap`,
run against production:

```
What I do: STALE   My work: STALE   About: STALE   Contact: STALE
4 of 4 swaps left the head stale at afterSwap
```

Every swap. The test had simply been getting away with it. Moving the sync to
`htmx:afterSwap` — which is strictly before the title update the test waits on — made the
same probe report `0 of 4`.

That is the first lesson, and it is cheap: **a test that passes on your machine has told you
about your machine.** CI's value here was not catching a typo. It was being a *different*
computer.

### "What does a deploy actually cost?"

The obvious next question, and the one that started the real work: while Compose replaces
the app container, what does a visitor see?

We had written "the gap is seconds" in the documentation. That was an estimate wearing a
measurement's clothes. So we measured it: an identical stack on a scratch port, and a poller
hitting the proxy as fast as curl would go — about 25 samples a second.

```
app container replaced: 1300 samples, 151 non-200
 codes: {'502': 151}
 first non-200 at +1.26s, window 8.40s wide
```

**8.4 seconds of 502 on every deploy touching app code.** Not seconds. Eight of them.

### Following the eight seconds

Split the window in two:

```
stop: 0.63s   start until serving: 6.61s
```

Stopping is free. Starting is not. Next question: is the app slow to start, or is Caddy slow
to notice the new container? Docker hands a restarted container a new IP, and a proxy that
caches DNS would 502 long after the app was ready.

```
uvicorn serving inside the container: 7.33s
…and then reachable through Caddy: +0.25s
```

Not the proxy. (That probe is coarse — it shells into the container in a loop — but a
quarter of a second is a decisive answer to "is this DNS?")

So: the app takes ~5 seconds to start serving, measured properly from the container's own
timestamped logs. Importing the application is only part of it:

```
1.56s to import app.main
```

Where do the other three seconds go? Into work that should have been done once, at build
time, and was instead being redone on every single container start:

```
site-packages .py: 747   .pyc: 343
```

**404 modules with no compiled bytecode** — all of FastAPI and Pydantic among them — plus
every module of the application itself. Python recompiled them from source on each boot.

The cause is two lines of Dockerfile in the wrong order:

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
...
RUN pip install --no-cache-dir -r requirements.txt
```

`PYTHONDONTWRITEBYTECODE` was set *before* `pip install`, so the install skipped compiling.
And the runtime container is deliberately read-only — `read_only: true`, `cap_drop: [ALL]`,
uid 10001 — so there was nowhere to cache the result afterwards either. The two hardening
choices combined into a permanent tax on every start.

The fix is to compile once, in the image:

```dockerfile
RUN python -m compileall -q /usr/local/lib/python3.13/site-packages /srv/app
# Only now: at runtime there is nowhere to write bytecode anyway.
ENV PYTHONDONTWRITEBYTECODE=1
```

Container start to accepting connections, from the container's logs: **5.11s → 2.83–3.05s**.

### Handing the rest to the proxy

Three seconds is still three seconds of 502. Compose has no rolling update, so the honest
options were to accept it or to make something else absorb it. Caddy will:

```caddyfile
reverse_proxy app:8000 {
	lb_try_duration 15s
	lb_try_interval 250ms
}
```

Now a request arriving mid-restart is held and retried rather than refused. A visitor gets a
slow page instead of a broken one, which is a trade worth making every time.

Measured again, same stack, same 25 samples a second:

```
app replaced, with proxy retries: 1565 samples, 0 non-200
  requests held longer than 0.5s: 1, slowest 3.72s
```

151 errors became zero, and the cost is a single request that took 3.7 seconds.

## Climax, part one: the config that never deployed

Except — how would that `Caddyfile` change ever reach production?

The `Caddyfile` is bind-mounted into the Caddy container. So we checked, before trusting it:

```
caddy container id before: b923f252e818
 Container gatecheck-caddy-1  Running
caddy container id after:  b923f252e818
```

`docker compose up -d` printed **Running** and kept the same container. Compose compares
images, environment variables and mount *definitions* — not the *contents* of a mounted
file. A `Caddyfile` edit changes nothing Compose can see.

Which means every `Caddyfile` change in this project's history had been committed, reviewed,
deployed, and silently ignored. Security headers. The `www` redirect. And now the retry
config that was supposed to fix the outage — it would have shipped and done nothing, and we
would have "verified" the fix by looking at a green pipeline.

The fix is to say so explicitly, and it turns out to be free:

```sh
docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile
```

```
caddy reload: 482 samples, 0 non-200
```

Zero-downtime by design — Caddy loads the new config and swaps it in without dropping
connections. The deploy now does this on every run.

## Climax, part two: the rollback that lied

The remaining hole was the one we had documented honestly and not yet fixed: the swap
happens, *then* the health check, *then* the tests. By the time anything is verified, the
new version is already live and the old container is gone. A bad deploy sits broken until a
human notices.

So we wrote a rollback: on failure, reset to the previous commit, rebuild it from cache,
wait for health. Then — because the one path that only runs when things are already going
wrong is the path most likely to be broken — we rehearsed it. A scratch clone, a local bare
origin, and a commit engineered to build perfectly and then refuse to serve:

```python
raise RuntimeError("deploy canary: this build must never serve")
```

A syntax error would not have done: the new `compileall` step rejects those at build time,
which is a nice accident of fixing the startup cost.

The rollback ran. Then:

```
checkout says: 2423960 Compile bytecode at build time...
but the container is running: Restarting (1)
site on 8082: 502
```

**The host was lying.** `git log` reported the good commit; a crash-looping container served
502 to every visitor. The worst of both worlds: broken, and claiming not to be.

The cause is a single line of `compose.yaml` that we wrote weeks earlier for a good reason:

```yaml
caddy:
  depends_on:
    app:
      condition: service_healthy
```

Because Caddy waits for the app to be healthy, `docker compose up` *itself* fails when the
new app container never gets there — and it fails **after** replacing it. Our rollback had
two branches: "the build failed, so nothing was touched" and "the container is unhealthy, so
roll back". This failure took the first branch and the second description. It reset the
checkout and never rebuilt.

The fix is to stop trying to tell the two apart:

```sh
roll_back() {
  echo "::error::$1"
  git reset --hard "$previous"
  if docker compose up -d --build && wait_healthy; then
    echo "rolled back; the site is serving $previous"
  else
    echo "::error::the rollback is unhealthy too - the site is down"
  fi
  exit 1
}

docker compose up -d --build || roll_back "compose up failed for $sha"
wait_healthy || { docker compose logs --tail 80 app; roll_back "$sha never became healthy"; }
```

There is no reliable way, from the host, to know whether the containers were replaced before
the failure. Rebuilding the previous commit is a no-op when they were not, and the only
correct action when they were. So do it unconditionally.

Re-rehearsed: the site ends at HTTP 200 on the previous commit, and the job exits 1. Both
exit codes checked, both ways round. A rollback is an incident, not a success.

## Recap: what it measures now

| | Before | After |
| --- | --- | --- |
| Container start → serving | 5.11s | 2.83–3.05s |
| App container swap, local, 25 Hz | 151 consecutive 502s over 8.4s | 0 errors, one request held 3.72s |
| App container swap, **production** | — | 3,482 samples, 0 non-200, slowest 0.16s |
| `Caddyfile` change reaching the proxy | never | graceful reload, 482 requests, 0 errors |
| Deploy confirmed good | ~25s | ~10s |
| Bad deploy | broken until noticed | detected in ~20s, previous commit rebuilt |

The shape of the pipeline, in the end:

```
push / PR ──► check ──► deploy ──► verify
              runner    droplet    runner
```

`check` builds the images and stands the whole stack up on the runner, then runs every suite
against it. It needs no secrets and touches nothing live, so it runs on pull requests too.
`deploy` needs `check` and is skipped for pull requests. `verify` re-tests production —
because the runner proved the *application*, and what is left to prove is that this host,
this proxy and this certificate are serving it.

### What we deliberately did not build

- **A registry.** Building on the droplet keeps one artefact and adds no credentials and no
  second place for the site to be stale. The cost is that `main` builds twice, adding a few
  minutes per merge. Worth it here; probably not at ten deploys a day.
- **A self-hosted runner.** A long-lived agent with a token on the droplet, to replace a
  60-second SSH session.
- **Blue-green.** One container per service, replaced in place. With the proxy absorbing the
  restart, the remaining benefit did not justify the machinery.

### Three things worth stealing

**Measure the number you are about to write down.** "The gap is seconds" survived review,
documentation and a commit message. It was 8.4 seconds. The first attempt to measure it was
also wrong — an API call inside the polling loop throttled sampling to 0.5 Hz and then hit a
rate limit — and reported a clean result that proved nothing. A measurement you have not
sanity-checked is a guess with a table around it.

**Rehearse the failure path.** Everything that only runs during an incident is, by default,
code that has never run. Ours was not merely broken; it was broken in the specific way that
makes the next debugging session harder, by leaving the host describing a state it was not
in. It took twenty minutes to rehearse and would have cost an evening to discover live.

**Ask what your orchestrator can actually see.** Compose diffs image IDs, environment and
mount definitions. It cannot see through a bind mount. Any config delivered that way needs
an explicit reload, or it is not deployed — it is just present. This generalises well beyond
Caddy: mounted config, `ConfigMap` contents, anything a supervisor holds by reference rather
than by value.

---

*The repository is [github.com/ivangetsitdone/website](https://github.com/ivangetsitdone/website).
The decisions summarised here live in [ADR-0010](../docs/adr/0010-continuous-deployment.md);
the operational detail is in [DEPLOY.md](../DEPLOY.md).*
