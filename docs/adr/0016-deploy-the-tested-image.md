# 16. Production runs the image the gate tested

Status: accepted

Supersedes the build-on-the-droplet half of [ADR-0010](0010-continuous-deployment.md).
Adopts for production what [ADR-0012](0012-preview-deployment.md) established for preview.

## Context

ADR-0010 had the droplet run `docker compose up -d --build`. The `check` job built and tested
the same commit on a runner minutes earlier, so the host rebuilt what had already been proven —
and the two could only be assumed to match. ADR-0015 closed the widest gap between them by
pinning the base images, but the gate still approved one artefact and another one shipped.

Routine deploys were not slow: measured at 8 seconds, because BuildKit found every layer
cached. The exposure was the cache-miss case. Change a frontend dependency or a photo and the
droplet runs `npm ci` and a Pillow pass over 81 images with roughly 678 MiB free — and
`roll_back()` rebuilt as well. The recovery path shared the failure mode of the thing it was
recovering from, on the box whose memory pressure was the likeliest cause.

Two transports were considered. Preview streams a `docker save` tarball over SSH, which has no
incremental: 59 MiB compressed on every deploy, against the ~12 MiB of layers a code change
actually moves. A registry ships only what changed.

## Decision

The `check` job publishes the image it tested to `ghcr.io/<repository>:<sha>`, and the droplet
runs that image.

- `compose.yaml` carries `image: ${APP_IMAGE:-website-app:local}` beside `build: .`, so local
  development still builds while production runs `--no-build`.
- The deploy writes `APP_IMAGE` into the untracked `.env`, beside `SITE_ADDRESS` and
  `COMPOSE_PROJECT_NAME`, and **pulls before touching anything**.
- Before the swap it tags whatever is serving as `<repository>:<previous sha>`. A rollback
  restarts that tag: no build, no registry, no network.
- Two assertions now close the run, not one: `HEAD` is the deployed commit, **and** the running
  container's image is the deployed tag.
- The host validates the image reference it is handed against
  `^ghcr\.io/[a-z0-9._/-]+:[0-9a-f]{40}$` rather than running what it is told.

## Consequences

- **What ships is what passed.** The artefact is identical, not equivalent, and the second
  assertion proves it rather than assuming it.
- **Rollback no longer builds.** It restarts an image that was running on this host minutes
  earlier, so it cannot fail for the reasons a rebuild can. This was the main point.
- **A registry outage is a failed deploy, not an incident.** The pull precedes every change, so
  the site keeps serving the previous commit and there is nothing to undo.
- **The droplet no longer needs a build toolchain's worth of memory.** It needs disk for a
  couple of image tags, which the deploy prunes to the one serving and the one a rollback needs.
- **GHCR becomes a deploy-time dependency.** It was already a build-time one through the base
  images; this moves it earlier and makes the failure cleaner.
- **The image is public,** like the repository and the assets inside it. A whitelabel instance
  wanting a private image would need the droplet to authenticate, which this does not do.
