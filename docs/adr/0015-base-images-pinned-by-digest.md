# 15. Base images are pinned by digest, and something watches each pin

Status: accepted

Builds on [ADR-0011](0011-dependency-hygiene.md).

## Context

Every Python and npm dependency is pinned exactly (ADR-0011), and the reasoning there is that
a pin makes the version a recorded decision rather than an accident of resolution. The base
images were the exception: `node:22-alpine`, `python:3.13-slim` twice, and `caddy:2-alpine`,
all floating tags.

That matters more here than on a host that builds once. Production still builds on the
droplet (ADR-0010), so `docker compose up -d --build` re-resolves those tags at deploy time —
minutes after the `check` job resolved them on the runner. The gate is real, but the image it
approved and the image that ships can differ. Nothing reports it, because nothing changed in
the repository.

The audit in ADR-0011 does not cover this either: `pip-audit` reads `requirements.txt` and
`npm audit` the lockfiles. A CVE in the base image's OpenSSL is outside both.

## Decision

Pin all four references by digest, keeping the tag alongside for readability
(`python:3.13-slim@sha256:...`), and give every pin a watcher.

- **The Dockerfile's three** are watched by Dependabot's `docker` ecosystem, added to
  `.github/dependabot.yml`. A moved tag arrives as a PR through the `check` gate.
- **Caddy's, in `compose.yaml`, is watched by a new `images` job in `audit.yml`.**
  Dependabot's docker ecosystem reads Dockerfiles, Containerfiles and Kubernetes manifests —
  not Compose files. Pinning it without a watcher would have traded a floating tag for a
  permanently stale one, which is worse than where we started.

`tests/test_image_pinning.py` asserts every registry image is digest-pinned, that both
Python stages carry the same digest, and that both watchers are configured.

## Consequences

- **A base image change is now a diff.** It is reviewed, it runs the gate, and it is in the
  history. The runner and the droplet build the same bytes.
- **The weekly audit can go red for a reason that is not a vulnerability.** A moved
  `caddy:2-alpine` fails the `images` job. That is consistent with ADR-0011 — a red audit
  means "a dependency needs attention", never "your change is bad" — and the fix is a
  one-line digest bump.
- **Pinning is only as good as the watchers.** A fourth image added to a Compose file, or a
  new Compose file, would be pinned by the test but watched by nothing. The test asserts the
  watchers exist; it cannot assert they are sufficient.
- **Digests are multi-arch indexes**, not single-platform manifests, so the pins do not tie
  the build to amd64.
