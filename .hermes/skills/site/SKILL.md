---
name: site
description: "Change the website: copy, services, contact details, colours. Live on the development site in seconds."
version: 1.0.0
author: the developer
metadata:
  hermes:
    tags: [website, copy, branding]
    related_skills: [todo, recent, ship]
---

# Change the site

## When to use

Ivan wants something on the website to read, look or say differently: a heading, a
paragraph, the services list, the phone number, the colours. `/site <what he wants>`, or any
plain request about the site.

## Where things live

Everything is under `/srv/website-dev`. **That directory is the development site**: save a
file and it is live at <https://dev.ivangetsitdone.com> within a couple of seconds, with no
commit and nothing published.

| Ivan wants to change | Edit |
| --- | --- |
| A page's heading, its one-line summary, or its search-engine description | `PAGES` in `app/main.py` — each entry is `(title, heading, description)` |
| The header links | `NAV` in `app/main.py`. Four at most; the reasoning is in the comment above it. |
| The two work-history tabs | `WORK_NAV` in `app/main.py` |
| The services and their one-liners | `SERVICES` in `app/main.py`. The home page shows the first three. |
| Body copy on a page | `app/templates/home.html`, `services.html`, `about.html`, `contact.html` |
| Colours | The custom properties at the top of `frontend/style.css`: `--brand` for buttons, `--eyebrow` for the small headings, `--bg` for the page |
| Photographs | Not by hand. Photographs are catalogue entries with a hash the build checks; `/todo add (dev)` it. |

**`app/static` and `app/media` are not live on the development site.** They are built from
`frontend/` and from the photo sources during the build, so a colour change shows on the
live site after `/ship`, not on dev. Say so rather than letting Ivan think it did not work.

## Procedure

1. **Make sure you have the facts.** A phone number, an address, a name: if Ivan has not
   given it, ask. Never invent one and never leave a guess on the site.
2. **Edit the file in place.** In templates change the words, not the markup, unless asked.
   In `app/main.py` touch only `PAGES`, `NAV`, `WORK_NAV` and `SERVICES`.
3. **If you edited `app/main.py`, check it still parses and the site still answers:**
   ```sh
   python3 -c "import ast; ast.parse(open('app/main.py').read())" &&
     sleep 3 && curl -s -o /dev/null -w '%{http_code}\n' https://dev.ivangetsitdone.com/healthz
   ```
   Anything other than `200`: put it back with `git checkout -- app/main.py`, tell Ivan it
   did not take, and `/todo add (dev)` a note.
4. **Confirm the change is live** by fetching the page and looking for the new words:
   ```sh
   curl -s https://dev.ivangetsitdone.com/about | grep -c 'the new wording'
   ```
5. **Tell Ivan what changed and which page to look at**, with the dev link. Do not mention
   file names unless he asks.
6. **Do not publish.** The development site is for looking. The live site changes only when
   Ivan says `/ship`.

## The licensing rule, which overrides everything above

Ivan holds no Oregon CCB licence. The pages that **offer** work — the home page's services
preview and the whole of `/services` — must never name regulated construction:

> remodel, sheetrock, drywall, tile, flooring, plumbing, electrical, painting, shower,
> install, repair, retaining wall

`tests/smoke.py` fails the build if one appears there, so a wording that breaks this cannot
be published — but it will waste Ivan's time and yours. The work-history pages describe past
work and are allowed to name it, because they say plainly that it is history rather than a
service on offer.

If Ivan asks for wording that offers regulated work, do not write it and do not soften it
into something that means the same thing. Tell him it needs the licence, and
`/todo add (dev)` it so the developer can look.

No prices, anywhere: he gives figures in person.

## Rules

- **Only `app/` and `frontend/`.** Everything else in the tree belongs to the developer and
  is read-only to you. If a request needs it, `/todo add (dev)` — that issue is the only way
  to reach them.
- Never `git add -A`, never commit, never push. `/ship` does the git work.
- Keep Ivan's voice. Match the tone already on the page unless he asks to change it.
- A request bigger than words and colours — a new page, a form, a map, a photograph — is a
  developer task. Say so and log it.

## Verification

The `curl … | grep -c` in step 4 prints a number above zero, and Ivan can see it at the link
you give him.
