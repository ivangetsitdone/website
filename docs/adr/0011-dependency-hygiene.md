# 11. Dependencies are audited weekly and pinned exactly

Status: accepted

Builds on [ADR-0010](0010-continuous-deployment.md).

## Context

Every dependency is pinned to an exact version — good for reproducible builds, and the whole
reason the image is byte-identical across rebuilds. The cost is that a pin never moves on its
own, so a vulnerability disclosed after the pin was chosen sits in the tree indefinitely.
That is not hypothetical: `starlette` 0.48.0, pulled in transitively by FastAPI, carried an
unauthenticated Range-header DoS (PYSEC-2026-1942) that every `/static`, `/media` and
`/print` response is exposed to. It was found only because someone finally ran `pip-audit`
by hand, months in.

## Decision

Two mechanisms, deliberately separate from the deploy pipeline.

- **Dependabot** (`.github/dependabot.yml`) opens weekly update PRs for four ecosystems: the
  runtime Python deps, the shipped frontend bundle, the browser-test toolchain, and the
  GitHub Actions themselves. Each PR runs the `check` gate like any other, so a bump that
  breaks a test cannot merge.
- **A scheduled audit** (`.github/workflows/audit.yml`) runs `pip-audit` and `npm audit`
  every Monday, and on demand. Its failure means "a dependency needs attention", decoupled
  from any code change.

`starlette` is now pinned explicitly rather than floated via FastAPI's `>=0.46.0`, so its
version is a decision recorded in `requirements.txt`, not an accident of resolution.

## Consequences

- **A new CVE never turns a code merge red.** The audit is on its own clock; `deploy.yml`
  does not gate on it. A merge and a vulnerability disclosure are different events and get
  different signals.
- **Dependabot PRs are real deploys once merged**, through the same gate and the same
  rollback as any change. The reviewer's job is to read the changelog, not to re-test.
- **Exact pins still mean manual intent.** Dependabot proposes; a human merges. Nothing
  auto-updates the running site.
- The audit is `--strict` for Python and `--audit-level=high` for npm. A finding below that
  bar does not fail the job; it waits for the Dependabot PR that raises the floor.
