# 19. Preview deployment is retired; the development site is the preview

Status: accepted. Supersedes [ADR-0012](0012-preview-deployment.md).

## Context

ADR-0012 built a way to look at a candidate before it shipped: a mutable `preview` branch,
a workflow dispatched from `main` with the candidate's SHA, a runner-built image streamed
over SSH to a forced-command user, a third container on the production network, and a
hostname. It was careful, and it was heavy: a wording change cost a branch push, a
dispatch and two builds. It also never ran. The environment secret it needed was never
created (#26), and the block that provisioned its user and keys ran inside every
production deploy regardless (#29).

ADR-0017 then answered the same question for one line of Compose: the development site
serves the working tree, so a change is on a URL the moment it is saved, with no commit.
ADR-0017 left preview in place and deferred the decision to retire it. Since then the
owner's assistant has shipped through the development site, and nobody has asked for
preview.

## Decision

Preview is removed, on the host and in the repository. The development site is the
preview.

- Gone from the repository: `preview.yml`, `compose.preview.yaml`,
  `scripts/deploy_preview.sh`, `deploy/preview_deploy.pub`, the preview virtual host in the
  Caddyfile, `PREVIEW_ADDRESS` everywhere, and the provisioning block in the deploy job.
- Gone from the host: the `preview-deploy` user and its home, the forced command in
  `/usr/local/sbin`, the `/srv/website-preview` checkout, the `website-preview` Compose
  project and its candidate images.
- Gone from GitHub: the `preview` branch and the `PREVIEW_ADDRESS` repository variable.
  The DNS record for `preview.ivangetsitdone.com` is the owner's to delete.
- Kept: the one assertion from the preview suite that was about production, that
  `deploy.yml` has no `workflow_dispatch` and deploys only from `main`. It lives in
  `tests/test_one_way_in.py`, in the gate.

## Consequences

- The deploy job is shorter and touches nothing but the site: no user management, no
  `sshd` introspection, no key rewriting after the site is already live. Issue #29 closes.
- One fewer account in the `docker` group, which §1a of DEPLOY.md calls root-equivalent.
  The host inventory loses three rows and one credential to rotate.
- "Look before you ship" is the development site, for everyone. What it cannot show,
  stylesheets, scripts and photographs, ADR-0017 already states; that limit is now the
  only one.
- ADR-0013's rule, production is never bounded tighter than what shares the host with it,
  is now measured against the dev site instead of the preview candidate.
