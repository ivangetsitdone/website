# 13. Production containers are bounded, and never tighter than preview

Status: accepted

Builds on [ADR-0008](0008-deployment.md) and [ADR-0012](0012-preview-deployment.md).

## Context

`compose.preview.yaml` has constrained the preview candidate since ADR-0012: 384 MiB of
memory, 0.75 CPU, 128 PIDs, a 64 MiB `/tmp`, and rotated logs. Production had none of
these. The hardening it did have — `read_only`, `cap_drop: [ALL]`, `no-new-privileges`,
an unprivileged uid — limits what a compromised container may *do*, not how much of the
host it may *consume*.

Measured on the live host: the app holds 39 MiB across 2 processes, Caddy 15 MiB across 6.
The site is the smallest thing on its own droplet. Of 1,962 MiB, roughly 1,284 MiB was in
use, and the largest consumers were other workloads sharing the box, not the site. A deploy
then builds images on that same host (ADR-0010), with `npm ci` and a Pillow pass over the
photo originals.

Unbounded, none of that is contained: the kernel's OOM killer chooses a victim by its own
heuristic, and the smallest, best-behaved process on the box is not the one it picks. Losing
`dockerd` or Caddy takes the site off the internet; losing the app does not.

Container logs were a smaller matter than it first appeared — `json-file` never rotates, but
measured growth is about 2.5 MiB/day against 38 GB free. Rotation is hygiene here, not a
fix for an imminent failure.

## Decision

Bound both production services, and keep one deliberate asymmetry.

- **`app`**: 512 MiB, 128 PIDs, `/tmp` capped at 64 MiB, logs rotated at 3 × 10 MiB.
- **`caddy`**: 128 MiB, 64 PIDs, the same log rotation.
- **No CPU cap on production.** Preview is capped at 0.75 precisely so a candidate cannot
  starve the live site on a single-vCPU host. Production is the service that should win.

`tests/test_production_runtime.py` asserts these against the *rendered* Compose config, and
asserts the cross-file invariant directly: production may never be given less memory or
fewer PIDs than preview.

## Consequences

- **A runaway app is killed as the app.** `restart: unless-stopped` and the healthcheck
  bring it back, and the deploy's rollback path still applies. That is a better failure than
  the kernel choosing among `dockerd`, Caddy and the app.
- **The ceilings are not sized to the app.** 512 MiB is roughly thirteen times the measured
  resident set. They are sized to leave the host room for a build and its neighbours; if the
  app ever legitimately needs more, that is a signal worth reading, not a number to raise
  reflexively.
- **Preview can no longer quietly out-resource production.** Raising the preview limits in
  `compose.preview.yaml` now fails the production test until production is raised too.
- **Applying this recreates both containers.** Replacing Caddy costs about 3.6 seconds of
  refused connections, as recorded in DEPLOY.md — a `Caddyfile` edit is a graceful reload,
  but a `compose.yaml` edit is not.
