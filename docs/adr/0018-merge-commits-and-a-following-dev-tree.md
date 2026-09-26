# 18. Pull requests merge with merge commits, and the development tree follows main

Status: accepted

Builds on [ADR-0017](0017-development-site-on-one-host.md).

## Context

The owner's assistant publishes by committing the shared tree's `app/` and `frontend/`
on a `hermes/<timestamp>` branch, opening a pull request and arming it to merge when
`check` passes. Two things were wrong with the first version of that.

Nothing made the merge wait. GitHub's auto-merge needs a required status check to wait
for; without one it either refuses to arm or merges at once. This repository had "Allow
auto-merge" on but no rule requiring `check` on `main`, so a pull request opened by hand
sat until someone merged it, and one opened by the assistant would have done the same.

And the change vanished from the development site the moment it was shipped. The script
switched the tree back to `main` after pushing, which put the files back to what `main`
had, and nothing pulled `main` into `/srv/website-dev` afterwards. The owner would watch
his edit disappear from the one URL he looks at.

## Decision

- **A ruleset on `main`** (`require_pr_workflow`: no deletion, no force push, required
  status check `check` from GitHub Actions, no bypass) is the thing auto-merge waits for.
  It is repository configuration, not code; DEPLOY.md records it.
- **Pull requests merge with merge commits**, not squash. The ship script arms with
  `--merge`, and after pushing it fast-forwards local `main` onto the shipped commit, so
  the tree keeps the change. Once GitHub merges, `origin/main` is a fast-forward of that
  local `main`; with squash it would not be, and every later pull would conflict.
- **The deploy brings the development checkout up to date.** The deploy job already runs
  as root on the droplet; its last step is `git pull --ff-only --autostash` in
  `/srv/website-dev`, with a warning rather than a failed deploy if that cannot be done.
  Root does it because the assistant may only write `app/` and `frontend/`, and a merge
  usually touches more than that.

## Consequences

- History on `main` gains a merge commit per pull request. The `(#NN)` subjects that
  squash produced are gone; the pull request number is in the merge commit instead.
- Direct pushes to `main` are refused for everyone, including the developer. Every change
  is a pull request, which is what the last dozen were anyway.
- The development site never loses a shipped change: it shows the local commit while the
  tests run, and the deploy fast-forwards the tree a few minutes later.
- If a squash or a rebase ever lands on `main` again, the dev tree's `main` diverges and
  the deploy's pull warns instead of following. The remedy is a `git reset --hard
  origin/main` in the dev tree after saving any unshipped edits, and not doing that again.
- The `recent` skill stays read-only. It reports; the deploy is what moves the tree.
