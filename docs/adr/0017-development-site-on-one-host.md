# 17. A development site serves the working tree, on the same host

Status: accepted

Builds on [ADR-0012](0012-preview-deployment.md) and [ADR-0016](0016-deploy-the-tested-image.md).

## Context

Looking at a change before it ships took a dispatched workflow, a mutable `preview` branch,
a forced-command SSH user, a runner-built image streamed over SSH and loaded beside the live
containers (ADR-0012). That machinery answers a real question, and it answers it slowly: a
wording change costs a branch push, a dispatch and two builds.

The scaffold this project seeded, `talosaether/whitelabel-site-generator`, answers it in one
line instead — its development host serves the working tree live, so an edit is on a URL as
soon as it is saved. Its ADR-0010 is explicit that **two hosts** are what make that simple,
and that the preview machinery existed precisely because its predecessor had one.

This project has one host, by decision, and it also has two agents working on it. The value
of a live development site here is less about saving a build than about making one agent's
work visible to the other, and to the owner, without a release.

## Decision

A development site at `dev.ivangetsitdone.com`, serving a second checkout at
`/srv/website-dev`, on the same machine as production.

Not the scaffold's overlay. That layers `compose.dev.yaml` over `compose.yaml` in one
project, including a Caddy with ports 80 and 443 — which production already holds here. So
`compose.dev.yaml` is a **standalone stack**, project `website-dev`, with no Caddy and no
published ports, joining `website_default` under the `dev-app` alias. Production's Caddy
proxies it, exactly as it already does for preview.

- **The source is mounted, the generated assets are not.** `app/main.py`, `app/templates`,
  `app/data` and `app/print` come from the tree, read-only. `app/static` and `app/media` are
  generated and git-ignored; mounting the tree over them would serve a site with no
  stylesheet, no script and no photographs, so they come from the image.
- **The dependencies are production's.** `APP_IMAGE` names the image the gate tested, so dev
  differs from production in source only.
- `uvicorn --reload`. A template edit is live on the next request; a `main.py` edit restarts
  the worker in about three seconds.
- Capped at 256 MiB and half a CPU. A reloading worker on a shared box must not be able to
  starve the live site.
- `X-Robots-Tag: noindex, nofollow, noarchive`, and canonical URLs still name production.

## Consequences

- **A copy or template change is visible in seconds, with no commit, no branch, no
  dispatch.** That is the whole point, and it is what makes the site useful to an agent
  working on the owner's behalf.
- **Stylesheets, scripts and photographs are not live.** They come from `APP_IMAGE`, so a
  change to `frontend/` or a new photograph shows only after a deploy, or after the watchers
  that would build them into the tree — deliberately deferred, because `npm ci` and a Pillow
  pass compete with the live site on a 2 GB box.
- **`_asset_versions` in `app/main.py` caches per process**, which is correct while assets
  come from a fixed image. A watcher that rewrites `app/static` would need that cache to
  stop being permanent.
- **Two configurations now share a machine, so separation is enforced rather than assumed.**
  The deploy strips `COMPOSE_FILE` from production's `.env` every run, and
  `tests/test_dev_overlay.py` asserts the strip, that `compose.yaml` contains no bind mount
  or `--reload`, that the dev stack publishes no ports, and that its mounts cover the source
  and not the generated directories.
- **The dev site is not private, only unindexed.** Nothing confidential belongs in the tree.
- **The tree is a shared workspace.** It is root-owned with ACLs granting the assistant
  write access to `app/` and `frontend/`; that boundary is host state, recorded in DEPLOY.md.
- Preview is untouched. If it turns out the dev site answers the same question more cheaply,
  retiring ADR-0012's machinery is a separate decision with its own record.
