# Handoff

Two assistants work on this site, and the development tree at `/srv/website-dev` is the live
development site. `git status` and `git diff` show *what* has changed; this file is for *why*,
and for questions passed between us. Newest entry first. Keep entries to a few lines, and
delete them once they are no longer useful.

This file lives under `app/`, which both assistants can write, so either can add an entry.

## Who does what

| | Claude Code (`root`) | Hermes (`hermes`) |
| --- | --- | --- |
| Talks to | the developer | Ivan, the site owner |
| Edits | anything | `app/` and `frontend/` — copy, `PAGES`/`NAV`/`SERVICES`, the palette |
| Cannot write | — | `compose*.yaml`, `Dockerfile`, `Caddyfile`, `.github/`, `tests/`, `scripts/`, `docs/`, `content/`, `.hermes/` |
| Ships by | pushing to `main`, or a pull request | `/ship`: a pull request that merges itself when `check` is green |
| Host account | `root` | unprivileged: no sudo, not in the `docker` group; ACLs on `app/`, `frontend/` and `.git/` |

Neither of us edits `/srv/website`. That is production, and only the pipeline changes it.

## How Hermes ships a change

Everything in the tree is already live on the development site, so Ivan sees an edit the
moment it is saved. Publishing is his `/ship`, which runs
`.hermes/skills/ship/scripts/ship.sh`: it stages **`app/` and `frontend/` by name**, commits,
pushes a `hermes/<timestamp>` branch, opens a pull request and arms auto-merge. The pull
request runs the full `check` job and merges only if it passes; a merge to `main` deploys.

**Consequence for the other assistant:** anything of yours left uncommitted under `app/` or
`frontend/` goes out with Ivan's next `/ship`. Keep infrastructure work out of those
directories, or commit it promptly. Stage files by name for the same reason — never
`git add -A` in this tree.

The skills live in `.hermes/skills/` (`site`, `todo`, `recent`, `ship`). They are in the
repository on purpose: the developer can read and change how the assistant works, and the
assistant cannot change its own instructions — `.hermes/` is root-owned and outside its
writable directories.

**The to-do list is GitHub issues.** `/todo add (dev) …` opens an issue labelled `dev`; that
label is how Hermes dispatches work to the developer, and the developer checks
`gh issue list --label dev` when starting. Hermes writes the title and the body and can
`edit` or `note` an issue later, so read the body, not just the title.

## What is not live on the development site

`app/static` and `app/media` are generated during the image build, so they come from
`APP_IMAGE` rather than from the tree ([ADR-0017](../docs/adr/0017-development-site-on-one-host.md)).
A colour change or a new photograph therefore shows on the live site after a deploy, not on
dev. Templates, `app/main.py`, `app/data` and `app/print` are live on save.

## Entries

- 2026-09-25 · Claude · Baseline skills added (`site`, `todo`, `recent`, `ship`), adapted from
  the `whitelabel-site-generator` scaffold. Photographs are **not** covered yet: the catalogue
  is hash-verified, so adding one is an entry plus a source file, not a file drop. A `photo`
  skill is drafted but parked until this baseline is in use — for now, a photograph from Ivan
  is `(dev)` work.
