# 10. Push to main deploys, over SSH, building on the droplet

Status: accepted

Supersedes the "CI/CD is not configured" note in earlier revisions of
[AGENTS.md](../../AGENTS.md). Builds on [ADR-0008](0008-deployment.md).

## Context

Deploying meant opening an SSH session and typing the same three commands, which is fine
until it is done at the wrong moment, in the wrong directory, or on the wrong host — all of
which had already happened. The repository is the only artefact and the droplet already
runs `docker compose` from a clone of it, so the gap between "merged" and "live" was purely
manual.

## Decision

`.github/workflows/deploy.yml` has three jobs.

**`check`** builds the images on the runner, starts the whole stack there over plain HTTP,
and runs all three suites against it. It touches nothing live and needs no secrets, so it
runs on pull requests as well as on `main`.

**`deploy`** needs `check`, and is skipped for pull requests. It opens one SSH session to
the droplet, resets the checkout to the exact commit that triggered the run, runs
`docker compose up -d --build`, and waits for the app container's own healthcheck to report
`healthy`. If anything in that fails, it resets to the previous commit, rebuilds it and
waits again, so the host is never left describing a version it is not serving. It then
reloads Caddy — a bind-mounted `Caddyfile` change does not otherwise reach the running
proxy — and asserts that `HEAD` is the commit it was asked to deploy.

**`verify`** re-runs the two HTTP suites against production. The application was already
proven on the runner; what is left to prove is that this host, this Caddy and this
certificate are serving it.

Deliberately **not** chosen:

- **A registry.** Building on the droplet keeps one artefact — the repository — and adds no
  credentials, no image retention policy and no second place for the site to be stale. The
  cost is that `main` builds twice, once on the runner and once on the droplet.
- **A self-hosted runner.** A long-lived agent on the droplet with a token, to replace a
  60-second SSH session.
- **Blue-green or a rollback path.** There is one app container and Compose replaces it in
  place. Rolling back is `git revert` and push, which is a full deploy through the same gate.

## Consequences

- **The droplet is a deploy target, not a workspace.** `git reset --hard` discards anything
  edited there. `.env` is untracked, so the `SITE_ADDRESS` pin survives.
- **Compose builds before it replaces.** The current containers keep serving for the whole
  build, and are replaced only once it succeeds, so a broken tree cannot take the site down.
  What it does not give is a tested new version running beside the old one: when the new
  container is unhealthy, the old one is already gone.
- **The app restart no longer shows.** Compose has no rolling update, so replacing the app
  container is a restart; what changed is who absorbs it. Two fixes, each measured on an
  identical stack while sampling the proxy 25 times a second:

  | | Before | After |
  | --- | --- | --- |
  | Container start → uvicorn serving | 5.11s | 2.83–3.05s |
  | Replacing the app container | 151 consecutive 502s over **8.4s** | **0 errors**, one request held 3.72s |

  Confirmed against production through a real deploy, not only in rehearsal: 3,482
  samples, zero non-200, slowest request 0.16s.

  The first is `python -m compileall` at build time: `PYTHONDONTWRITEBYTECODE` was set
  before `pip install` and the runtime filesystem is read-only, so 404 of 747 modules —
  all of FastAPI and Pydantic among them — were recompiled from source on every start. The
  second is `lb_try_duration` on the reverse proxy, which holds the connection and retries
  instead of returning 502.
- **Replacing Caddy itself still costs 3.6s of refused connections**, because nothing is
  left to absorb it. That only happens when `compose.yaml` changes; a `Caddyfile` change is
  a graceful reload, measured at 482 requests through a reload with zero errors.
- **A deploy that will not serve is rolled back, not left.** The checkout returns to the
  previous commit and it is rebuilt from cache. Every failure path rolls back the same way,
  because there is no reliable way to tell from the host whether the containers were
  replaced before the failure: `caddy` declares `depends_on: app: condition:
  service_healthy`, so `docker compose up` itself fails once the new app container is in
  place and failing. Rebuilding the previous commit is a no-op when nothing was replaced,
  and the only correct action when something was. The job fails either way — a rollback is
  an incident, not a success.
- **Old images do not accumulate; build cache would.** Each deploy prunes the image the
  previous one left untagged, and trims build cache older than a week. Both matter on a
  2 GB droplet, and the deploy prints `df -h /` so a filling disk is visible before it bites.
- **Two secrets are the whole trust model**: `DEPLOY_KEY`, whose public half sits in the
  droplet's `authorized_keys`, and `DEPLOY_KNOWN_HOSTS`, which pins the host key so the
  runner cannot be talked into deploying to somewhere else. Rebuilding the droplet means
  re-adding the public key and refreshing the host key. The key is not restricted with
  `command=` in `authorized_keys`; it is a root shell on the droplet, and anyone who can
  push to `main` already controls what runs there.
- **The checkout path is fixed at `/srv/website`**, matching `scripts/bootstrap.sh` and
  `cloud-init.yaml`. A droplet with it anywhere else fails the deploy on the first command,
  and the fix is to move the checkout, not to teach the workflow another path.
- **Bind-mounted config is invisible to Compose.** It compares images, environment and
  mount *definitions*, not the contents of a mounted file, so `docker compose up -d` after a
  `Caddyfile` edit prints "Running" and keeps the same container. Every `Caddyfile` change
  before this was accepted, deployed and silently ignored.
- Documentation-only pushes still trigger a run. Nothing under `docs/` is copied into the
  image, so every layer is cached, the image ID does not change and Compose recreates
  nothing — the deploy is a no-op that still proves the site is up.
