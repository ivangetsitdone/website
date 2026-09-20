# 12. Preview deploys use a trusted workflow and host-owned policy

Status: accepted

## Context

Photo ingestion needs human review of titles, captions, ordering and before/after groupings before a batch reaches the public gallery. Pull-request checks prove the application works, but they do not give the owner a URL that renders the proposed catalogue. Editing the production checkout or deploying a feature branch over the production app would bypass the existing main-only release gate.

A workflow and Compose file taken from the mutable preview branch would not be isolation: that branch could change the workflow, steal a deployment key, mount host paths, or replace production through the Docker daemon.

## Decision

A mutable `preview` branch identifies the candidate, but it never defines its own deployment policy. `.github/workflows/preview.yml` is dispatched explicitly from `main` with the exact current preview commit. Candidate tests run without deployment secrets. The deploy job uses a separate `PREVIEW_DEPLOY_KEY` stored in a GitHub `preview` environment restricted to `main`.

The key logs in as `preview-deploy` and is restricted in `authorized_keys` to the root-owned `/usr/local/sbin/website-preview-deploy` command. Production deploys install that command and provision the dedicated account from the reviewed public key in `deploy/preview_deploy.pub`, only after production is healthy. The candidate image is built and tested on an isolated GitHub runner, capped at 600 MB, exported with a SHA-256 checksum, and streamed to the forced command. The host verifies the checksum and exact `origin/preview` SHA, loads the image, and runs the trusted `/srv/website/compose.preview.yaml`; candidate Dockerfiles never execute on the production droplet.

The isolated `preview-app` container joins the existing production Compose network under that alias. The production Caddy instance serves `preview.ivangetsitdone.com`, proxies only that hostname to the preview container, and sends `X-Robots-Tag: noindex, nofollow, noarchive`.

## Consequences

- Preview candidates cannot change the workflow that receives the SSH key or the Compose policy used on the host.
- The preview credential is separate from production and can execute only the host-owned deployer. The `preview` GitHub environment must allow deployments from `main` only; optional required reviewers add another approval gate.
- Production remains `/srv/website`, the `app` service and the `main` branch. Preview uses `/srv/website-preview`, `preview-app` and the `website-preview` Compose project.
- The preview branch is mutable review state, not release history. Approved work still reaches production through a pull request to `main`, green checks, merge, deploy and verification.
- Preview responses are unindexed but not private. Only photos already authorized for public disclosure may be deployed there; add authentication before using it for confidential material.
- The Cloudflare `preview` A record must point to the droplet and remain DNS-only so Caddy can answer the TLS-ALPN challenge.
- The network name `website_default` is deliberate: `/srv/website` is the fixed production checkout and Compose project name. A renamed production project would also require updating `compose.preview.yaml`.
