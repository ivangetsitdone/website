---
name: recent
description: "What changed on the website lately, and whether it has reached the live site."
version: 1.0.0
author: the developer
metadata:
  hermes:
    tags: [website, status]
    related_skills: [site, todo, ship]
---

# Recent changes

```sh
bash .hermes/skills/recent/scripts/recent.sh
```

Relay the output as it is. What the three sections mean, if Ivan asks:

- **ON DEV** — saved in the working copy and visible at
  <https://dev.ivangetsitdone.com>, not yet on the live site. `/ship` publishes it.
- **WAITING** — published and being tested. It merges and goes live by itself if the tests
  pass, usually within five minutes.
- **PUBLISHED** — live at <https://ivangetsitdone.com>. `published` means it went out;
  **`FAILED`** means it did not, nothing changed on the live site, and the developer needs
  to look: `/todo add (dev) …` with what the line said.
