# 14. The Compose project name is an isolation boundary

Status: accepted

Builds on [ADR-0008](0008-deployment.md) and [ADR-0010](0010-continuous-deployment.md).

## Context

Compose names a project after its working directory unless told otherwise. Production runs
from `/srv/website`, so its project was `website`. Any clone of this repository into a
directory also called `website` — the name `git clone` picks by default — inherited that
name and addressed the same containers.

On a host where a development checkout sits beside the live site, this was live and silent:

```console
$ cd /root/dev/website && docker compose ps
website-app-1     Up 16 hours (healthy)
website-caddy-1   Up 10 minutes
```

`docker compose up -d --build` from that clone rebuilds production, `down` stops the site,
and `down -v` deletes the `caddy_data` volume holding the TLS certificate. None of those
commands name `/srv/website`, so the rule that the droplet's checkout belongs to the
pipeline could be broken without touching the path — and these are the commands this guide
tells you to run.

Two fixes were rejected:

- **Pin `name: website` in `compose.yaml`.** Makes every clone collide regardless of its
  directory, removing the accidental safety a differently-named directory gave.
- **Rename production to `website-production`.** Actually isolates clones, but
  `compose.preview.yaml` joins the external network `website_default` — Compose's default
  network for a project called `website`. Renaming production silently breaks preview's
  route, and needs a migration that orphans the running containers while they still hold
  ports 80 and 443.

## Decision

Invert the default: the file names a project that is **not** production's, and production
opts back in.

- `compose.yaml` declares `name: website-local`. Any clone gets that, whatever its directory.
- The deploy checkout sets `COMPOSE_PROJECT_NAME=website` in its untracked `.env`, which
  survives `git reset --hard`. `scripts/bootstrap.sh` writes it on a fresh host, and
  `deploy.yml` ensures it before any Compose command runs.

Precedence makes this work: `COMPOSE_PROJECT_NAME` beats the file's `name:`, which beats the
directory.

## Consequences

- **No rename and no migration.** The live containers keep the project `website`, so
  `website_default` keeps its name and preview is untouched.
- **A clone is safe by default,** including one in a directory called `website`. Being
  unsafe now takes a deliberate edit to an untracked file.
- **`.env` is load-bearing on the droplet.** It already pinned `SITE_ADDRESS`; it now also
  decides which checkout is the live one. The deploy rewrites the line every run, so a lost
  or hand-edited `.env` self-heals on the next deploy rather than quietly splitting the stack.
- **Anything reading container names must not assume `website-`.** The `check` job on the
  runner now builds under `website-local`; it addresses services through Compose, so it is
  unaffected.
- `tests/test_production_runtime.py` asserts both halves, including that the preview network
  still names the production project — renaming one without the other fails the suite.
