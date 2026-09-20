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
`healthy`.

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
- **There is a visible restart.** Replacing the app container leaves Caddy briefly proxying
  to nothing. Measured over a real deploy, the gap is seconds; Caddy answers 502 inside it.
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
- Documentation-only pushes still trigger a run. Nothing under `docs/` is copied into the
  image, so every layer is cached, the image ID does not change and Compose recreates
  nothing — the deploy is a no-op that still proves the site is up.
