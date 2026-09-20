# Zip, LLC — ivangetsitdone.com

The website for Ivan Pineda's small-jobs business in Forest Grove, Oregon: yard work,
hauling, pressure washing, gutters and moving help, plus a photo record of the bigger
work he has done. Six pages, server-rendered, no database, no contact form — the site's
job is to get someone to call or text.

**Live:** <https://ivangetsitdone.com> (`www` redirects to the bare domain)

> ### Read this before editing any public copy
>
> Ivan holds a business registration but **no Oregon CCB contractor licence**. Oregon law
> conditions the small-job exemption on *not* advertising as a contractor, so the site
> advertises only unregulated work and presents the photo archive as past experience.
> The test suite fails if regulated trades reappear in the blocks that offer work, or if
> the disclosure goes missing from any page.
>
> **[ADR-0003](docs/adr/0003-licensing-constraint.md) explains what may and may not be
> said, and why.** Open questions for the owner and the CCB are in
> [docs/open-questions.md](docs/open-questions.md).

## Run it

Requires Docker Engine with Compose v2. Nothing else — Node, Python and Pillow all run
inside the build.

```sh
git clone https://github.com/ivangetsitdone/website.git
cd website
printf 'SITE_ADDRESS=:80\nWWW_ADDRESS=:8080\n' > .env   # plain HTTP; omit for the real domain
docker compose up -d --build
curl -s -o /dev/null -w '%{http_code}\n' http://localhost/     # 200
```

First build takes about five minutes: Vite bundles the frontend, then Pillow regenerates
75 images from the tracked originals. `docker compose logs -f` to watch.

Deploying to a server is [DEPLOY.md](DEPLOY.md) — one command on a fresh droplet.
After that it is automatic: **every push to `main` is built and tested on a runner, then
deployed**, and production is re-checked afterwards. Pull requests run the tests and stop
there. See [Automatic deploys](DEPLOY.md#2a-automatic-deploys).
The droplet is a deploy target, not a workspace — the deploy resets `/srv/website` to the
pushed commit, so anything edited there is discarded.

## How it fits together

| Layer | What |
| --- | --- |
| Server | FastAPI + Jinja2. One route renders all six pages from `PAGES` in `app/main.py`. |
| Navigation | HTMX `hx-boost` swaps the body; `frontend/main.js` keeps `<title>`, description and canonical in sync. |
| Assets | Vite bundles `frontend/` to `app/static/site.{js,css}`. Vue is installed but no component is mounted. |
| Images | `scripts/build_photos.py` turns tracked originals into metadata-free WebPs at build time. |
| Serving | Caddy terminates TLS, adds security headers, proxies to the app. Certificates are automatic. |

The Dockerfile has three stages — Node assets, Pillow images, Python runtime — so the
runtime image carries neither toolchain. The app runs as uid 10001 on a read-only
filesystem with all capabilities dropped.

## Where things live

```text
app/main.py              Routes, and all page copy: PAGES, SERVICES, NAV, REGISTRY, LICENSE_NOTE
app/templates/           page.html is the layout; one partial per page, plus gallery.html
app/data/portfolio.json  Photo catalogue: captions, categories, stages, SHA-256 of every source
app/print/               Hand-authored printable SVG, served from /print
frontend/                style.css, gallery.css, gallery.js (the viewer), main.js (HTMX glue)
content/photos/          35 original JPEGs — tracked, never served
content/portraits/       About-page portrait source
content/brand/           Logo and business-card originals
scripts/build_photos.py  Image pipeline; verifies hashes, strips metadata
scripts/bootstrap.sh     Stand the site up on a fresh host
tests/                   Two dependency-free HTTP suites, plus Playwright
docs/adr/                Why things are the way they are
.github/workflows/       Deploy on push to main, then test the live site
DEPLOY.md                Rebuilding on a new host
```

`app/static/` and `app/media/` are generated during the build and are **not** tracked.
`recovery/` is local scratch — logs, screenshots, Playwright browsers — and is ignored.

## Editing content

- **Page copy** is Python, not templates: `PAGES` (title, heading, description per page)
  and `SERVICES` in `app/main.py`.
- **Photos** are `app/data/portfolio.json`. Edit captions, categories, stages and project
  groupings there; the `sha256` of each source is checked at build time, so a swapped or
  corrupted original fails the build rather than shipping quietly.
- **Adding a photo** means putting the original in `content/photos/`, adding an entry with
  its hash, and rebuilding. Don't re-run the one-time importer over editorial edits.
- **Brand artwork** is `content/brand/`, with hashes in the same catalogue. Replacing the
  business card is: swap the file, update `sha256` and `alt`, rebuild.

After any copy change, run `tests/smoke.py` — it is the licensing guardrail, not just a
health check.

## Tests

Three suites, all pointing at `https://ivangetsitdone.com` by default; pass a base URL to
test somewhere else.

```sh
python3 tests/smoke.py                      # pages, headers, caching, licensing guardrails
python3 tests/portfolio_http.py             # 35 sources, 75 generated assets, source isolation
cd tests/browser && npm ci
PLAYWRIGHT_BROWSERS_PATH=../../recovery/browsers npx playwright install chromium
npm test                                    # 30 tests, desktop + mobile, axe WCAG 2 A/AA
```

The Python suites need no dependencies at all. To point them at a local preview:

```sh
python3 tests/smoke.py http://localhost
BASE_URL=http://localhost npm test
```

What the browser suite covers: boosted navigation and history, head-metadata sync, the
gallery filters and carousel, keyboard focus and the skip link, the no-JavaScript
fallback, responsive layout at nine widths, and axe accessibility checks on every content
page and the open viewer. It is not a substitute for real-device or Safari testing, which
has never been done here.

## Writing

Build-in-public write-ups of problems solved in this repository are in
[blog/](blog/README.md), newest first. They are not part of the site and are not copied
into the image.

## Decisions

Short records of why the non-obvious choices were made, in [docs/adr](docs/adr):

| # | Decision |
| --- | --- |
| [0001](docs/adr/0001-server-rendered-not-spa.md) | Server-rendered FastAPI + HTMX, not a static SPA |
| [0002](docs/adr/0002-photo-pipeline.md) | Originals tracked and hash-verified; derivatives generated, never committed |
| [0003](docs/adr/0003-licensing-constraint.md) | Unlicensed-contractor constraint, enforced by tests |
| [0004](docs/adr/0004-four-link-navigation.md) | Four visible links, nothing hidden behind a menu |
| [0005](docs/adr/0005-scroll-snap-carousel.md) | Scroll-snap carousel rather than the native CSS one |
| [0006](docs/adr/0006-asset-cache-versioning.md) | Content-versioned asset URLs and explicit cache headers |
| [0007](docs/adr/0007-no-published-rates.md) | No prices on the site, deliberately |
| [0008](docs/adr/0008-deployment.md) | Docker Compose + Caddy on a single droplet |
| [0009](docs/adr/0009-brand-assets.md) | Brand artwork processed at build time, not by hand |
| [0010](docs/adr/0010-continuous-deployment.md) | Push to main deploys over SSH, building on the droplet |
| [0011](docs/adr/0011-dependency-hygiene.md) | Dependencies audited weekly and pinned exactly |

## Business facts

These are confirmed and appear in the site's copy. Don't infer beyond them.

- **Zip, LLC** — Oregon registry **2249807-97**, registered 2024-04-04
- **971-288-3488** — calls and texts both welcome
- Forest Grove and surrounding communities, 30-mile radius; evenings and weekends
- Not a CCB-licensed contractor (see the warning above)

## Conventions

- Keep source, config, tests and decisions in the repository. Never commit secrets,
  dependencies, generated assets or raw session logs.
- `recovery/` is for local diagnostics and is ignored by both Git and Docker.
- Don't run `docker compose down -v` — it deletes Caddy's certificate volume and burns a
  rate-limited re-issue.
