---
name: todo
description: "The website to-do list: show it, add to it, reword an item, add a note, or mark it done."
version: 1.0.0
author: the developer
metadata:
  hermes:
    tags: [website, todo, issues]
    related_skills: [site, recent, ship]
---

# To-do list

The list is this repository's GitHub issues. An item marked **(dev)** is work for the
developer, who watches the `dev` label; anything else is for Ivan or for you. The script is
the only thing that touches the list.

| Ivan says | Run, from `/srv/website-dev` |
| --- | --- |
| `/todo` | `bash .hermes/skills/todo/scripts/todo.sh` |
| `/todo add <text>` | `bash .hermes/skills/todo/scripts/todo.sh add "<title>" "<details>"` |
| `/todo edit <n> <text>` | `bash .hermes/skills/todo/scripts/todo.sh edit <n> "<title>" "<details>"` |
| `/todo note <n> <text>` | `bash .hermes/skills/todo/scripts/todo.sh note <n> "<text>"` |
| `/todo done <n>` | `bash .hermes/skills/todo/scripts/todo.sh done <n>` |

Relay the output as it is.

## Writing an item

An item has a **title** and **details**, like a ticket. You write both: Ivan talks in plain
sentences and it is your job to turn that into a tidy entry.

- **Title:** one line, under 90 characters, the outcome in plain words. `Contact page: add
  the second phone number`, not the whole request. The script refuses a longer one.
- **Details:** what Ivan asked for, in his words where they matter, plus anything the person
  doing it will need — which page, what it should say, the path of any file he sent. For a
  developer item this is the whole brief: that issue is how the developer hears about it,
  there is no other channel.
- **Start the title with `(dev)`** when it needs the developer — anything outside copy, the
  `PAGES`/`NAV`/`SERVICES` blocks and the colours. That adds the `dev` label. On `edit`, an
  item already marked `(dev)` stays that way.

`edit` with an empty title (`""`) keeps the title and replaces the details. `note` adds a
comment, for things learnt after the item was written: a decision, a second file, a change of
mind. Prefer `note` over rewriting details the developer may already have read.

When Ivan corrects an item or gives more information, update it without being asked.
