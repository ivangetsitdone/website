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

`.github/workflows/deploy.yml` runs on every push to `main`. It opens one SSH session to
the droplet, resets the checkout to the exact commit that triggered the run, runs
`docker compose up -d --build`, and waits for the app container's own healthcheck to report
`healthy`. Then two follow-on jobs run the existing suites against the live site.

Deliberately **not** chosen:

- **A registry.** Building on the droplet keeps one artefact — the repository — and adds no
  credentials, no image retention policy and no second place for the site to be stale.
  A 2 GB droplet builds it in about five minutes, and the running containers are untouched
  until the build succeeds.
- **A self-hosted runner.** A long-lived agent on the droplet with a token, to replace a
  60-second SSH session.
- **A test gate before deploying.** The build itself is the gate: the photo pipeline
  verifies every source hash, so a broken tree fails `docker compose up --build` and the old
  containers keep serving. Running the suites against a throwaway stack on a pull request is
  the obvious next step and is not done yet.

## Consequences

- **The droplet is a deploy target, not a workspace.** `git reset --hard` discards anything
  edited there. `.env` is untracked, so the `SITE_ADDRESS` pin survives.
- **Tests run after the deploy, against production.** A red `verify` job means something
  already reached the live site — read it as "fix forward", not "the deploy was blocked".
  The licensing guardrails in `tests/smoke.py` are the reason this matters.
- **Two secrets are the whole trust model**: `DEPLOY_KEY`, whose public half sits in the
  droplet's `authorized_keys`, and `DEPLOY_KNOWN_HOSTS`, which pins the host key so the
  runner cannot be talked into deploying to somewhere else. Rebuilding the droplet means
  re-adding the public key and refreshing the host key. The key is not restricted with
  `command=` in `authorized_keys`; it is a root shell on the droplet, and anyone who can
  push to `main` already controls what runs there.
- **The droplet's checkout path is not fixed.** The remote script tries the `DEPLOY_DIR`
  repository variable, then `/srv/website`, then `/root/website`, because it has lived in
  more than one of them.
- Documentation-only pushes still trigger a run. Nothing under `docs/` is copied into the
  image, so every layer is cached, the image ID does not change and Compose recreates
  nothing — the deploy is a no-op that still proves the site is up.
