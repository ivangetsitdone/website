---
name: ship
description: "Publish the changes on the development site to the live site."
version: 1.0.0
author: the developer
metadata:
  hermes:
    tags: [website, publish]
    related_skills: [site, recent, todo]
---

# Publish to the live site

`/ship` means Ivan has looked at <https://dev.ivangetsitdone.com> and wants it live.
Everything under `app/` and `frontend/` that differs from what is published goes out
together.

Run it from `/srv/website-dev` with a short description of what is being published:

```sh
bash .hermes/skills/ship/scripts/ship.sh "new home headline and phone number"
```

It stages `app/` and `frontend/` by name, commits, pushes a branch, opens a pull request and
arms it to merge itself once the tests pass. Merging publishes.

Relay what the script prints. Then tell Ivan: the tests take about two minutes and publishing
about three more, `/recent` shows whether it went through, and if it says FAILED nothing
changed on the live site and the developer needs to look — `/todo add (dev) …`.

Never run the git commands by hand. The script is the whole procedure, and it stages only the
two directories you are allowed to change — the tree is shared with the developer's
assistant, and `git add -A` would publish their work in progress along with Ivan's.

## If it says there is nothing to publish

Then nothing under `app/` or `frontend/` differs from the live site. Either the change was
already published, or it was made somewhere else. Check with `/recent`.
