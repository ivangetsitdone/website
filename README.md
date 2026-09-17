# Contractor Site

A mobile-first contractor services website, recovered from an interrupted development session on 2026-09-17.

## Public domain — verified 2026-09-17

`https://ivanpineda.bottah.dev` is now the default Compose/Caddy address. DNS A resolves to this droplet; no AAAA record was returned. Caddy obtained a Let's Encrypt certificate for this hostname (current expiry 2026-12-16) and redirects HTTP to HTTPS with 308. HTTPS `/healthz` passed with normal certificate verification from this host. Logs: ignored `recovery/domain-caddy.log`. Caddy retains/renews certificates in its existing named volumes; no firewall or other host settings changed. Test defaults now point at this HTTPS hostname. For a local HTTP-only preview, set `SITE_ADDRESS=:80` before `docker compose up -d`.

## Site content — replaced and verified, 2026-09-17

The Hello World demonstration is gone from the public site. Home, services, about and contact now carry real business copy in dedicated templates (`app/templates/home.html`, `services.html`, `about.html`, `contact.html`) with a rebuilt stylesheet, a hero photo from the project album, a services list rendered from `SERVICES` in `app/main.py`, and a scope note stating that some work may need permits or a licensed specialist.

- Removed with the demo: the `/hello` fragment route (now 404), `app/templates/hello.html`, `frontend/Hello.vue` and the Vue mounting/unmounting code in `frontend/main.js`. `vue` and `@vitejs/plugin-vue` stay installed and configured so a single-file component can be added where interaction needs one; no component is mounted today. HTMX still drives boosted navigation.
- Each page emits its own `<meta name="description">` and `<link rel="canonical">` (`https://ivanpineda.bottah.dev/...`). Because boosted navigation swaps the body only, `frontend/main.js` copies both from `main[data-description]`/`main[data-canonical]` after every swap; browser tests assert head and body stay in sync.
- The About page portrait is built from `content/portraits/ivan-pineda.jpg` through the same Pillow build stage as the album: hash-verified, resized to at most 900×900 and written as one metadata-free `/media/ivan-pineda.webp`. The original is never served. **Its authorization is unconfirmed — see `content/README.md` before promoting the site.**
- Verified after the change: `docker compose up -d --build` (log: ignored `recovery/content-build.log`), HTTP smoke checks, catalog/asset checks (71 WebP assets, 8.36 MiB, source isolation including `/content/portraits/`), and 22 Chromium tests at desktop and mobile sizes. Axe WCAG A/AA checks now cover home, services, about and contact as well as the gallery, and report no violations; that is not a full accessibility audit, and no real device or Safari was tested. Desktop and mobile screenshots for home, about and contact were reviewed under ignored `recovery/`.
- Test defaults now target `https://ivanpineda.bottah.dev` instead of `http://localhost`. Pass a base URL argument (or `BASE_URL`) to test a local HTTP-only preview.

### Copy awaiting owner confirmation

These statements are live on the site but are **not** recorded as confirmed anywhere in this repository; they came from the previous session's conversation, whose context was lost. Confirm each one with the owner:

- “10+ years” of hands-on experience, and experience in general construction and sheetrock repairs.
- Availability limited to evenings and weekends around a full-time job.
- The personal note about supporting his family and saving for his daughter's college fund.
- The surname spelling **Pineda** (used in copy, the footer and the domain) — `content/README.md` still records the Pineda/Pidena ambiguity.
- Publishing the About page portrait.

## Confirmed business details

- Public business name supplied by owner: **Zip LLC Handyman Services**. Used in site header, page titles and footer. Rebuilt preview and reran HTTP smoke checks and all four browser tests successfully after branding change (2026-09-17).
- Supplied contact name: Ivan Pineda; supplied profile: https://nextdoor.com/profile/01TRMJKkx92rDy-wW (not fetched or republished).
- Confirmed service area: Forest Grove and surrounding communities within a 30-mile radius. Displayed on home and services pages; no state or specific neighboring cities inferred. Rebuild, HTTP smoke checks (including service-area assertions), and all four browser tests passed after this update.
- Owner-described experience: showers, flooring, fencing, basic plumbing fixture replacement, basic electrical work, and interior/exterior painting. Listed on services page without inferring specific shower/electrical tasks or licensing. Confirm permitted scope and any licensing requirements before expanding claims. Services update rebuilt successfully; HTTP checks (including service text) and all four browser tests passed.
- Confirmed public phone: **971-288-3488**. Owner confirmed calls and texts are welcome. Click-to-call and SMS links on home and contact pages. Rebuild, HTTP checks (including phone/SMS links), and four browser tests passed after SMS update. Actual telephone dialing and SMS handoff/delivery are not tested.
- Still needed: optional public email and domain. Uploaded portfolio photos were authorized for this site; Nextdoor text/photos have not been imported or authorized separately. Do not infer credentials or publish unconfirmed contact details.

## Portfolio — deployed and verified, 2026-09-17

- `/portfolio`: 35 selected photos from 54 owner-supplied uploads, with original captions, category/stage filters and a responsive grid. Native-dialog viewer supports previous/next, arrow keys, Escape, focus return and contained keyboard focus. Photo links and captions work without JavaScript.
- `/before-after`: six projects labelled “Project / 01…”: side-yard clearing, garden steps, the shower remodel, sidewalk clearing, parking-lot restriping and exterior painting. The owner confirmed the shower project's two **before** photos and the three before/after pairs (sidewalk, parking lot, siding); the shower's tile photos are still explicitly **in progress**, not finished. The first two groupings and the remaining captions still need owner review; “Detail” does not claim a completed job.
- Original selected JPEGs, SHA-256 provenance and editable catalog are in Git. Docker generates 70 metadata-free WebPs (8.31 MiB total; each under 500 KB); the grid uses lazy thumbnails and the viewer loads the larger image on demand. Original JPEGs are not in the runtime image or served publicly.
- See `content/README.md` for selection decisions, uncertainties and reconstruction. Edit `app/data/portfolio.json` for captions/order/stages; don't rerun the one-time importer over editorial edits. Raw uploads and unselected images remain in ignored `recovery/uploads/`.
- Compose rebuild, HTTP smoke checks, 70-image/source-isolation checks, and 16 Chromium tests pass at desktop/mobile sizes. Tests cover filters/empty results, viewer controls/focus, failed images, HTMX history, no-JS fallback and all thumbnail decoding. Axe WCAG A/AA checks report no violations on the gallery and open viewer; this is not a full accessibility audit or real-device/Safari verification. Desktop/mobile screenshots were visually reviewed; evidence is ignored under `recovery/`.
- No additional host packages installed for image processing: Pillow runs only in a disposable Docker build stage. Build logs: `recovery/portfolio-build.log`, `recovery/portfolio-rebuild.log`.
- Original surname spelling needs confirmation (Pineda/Pidena); public attribution uses the confirmed business name. Local Git is still not an off-host backup; keep the MacBook originals.

## Mission

First prove a working **Hello World** stack: FastAPI + Jinja server rendering, HTMX navigation/partial updates, Vue 3 single-file components only where useful, and locally bundled assets. Package it with Docker Compose and Caddy. Then iterate on services, about, contact, portfolio, and before/after pages using real business details and authorized photos.

**Architecture clarification:** the original request also said “static completely self contained SPA.” The previous assistant interpreted this as self-contained assets and SPA-like navigation, not a purely static/offline application. FastAPI server rendering requires a server. Confirm this interpretation before expanding scope.

No GitHub repository or CI/CD yet; local Git checkpoints are for recovery.

## Verified runtime — 2026-09-17

- Droplet upgraded by owner to 2 GB (1.9 GiB visible); no swap. Chromium test libraries/fonts installed on the host using `cd tests/browser && npx playwright install-deps chromium`; installation log is in ignored `recovery/browser-system-deps.log`. No swap/firewall changes.
- `docker compose config --quiet` and `docker compose up -d --build` passed. App is healthy and Caddy is running; `curl -fsS http://localhost/healthz` returns `{"status":"ok"}`.
- Preview listens on host port 80: `http://<droplet-ip>/` (external firewall/reachability not yet tested). No domain or HTTPS verified.
- Build logs: ignored `recovery/resume-build.log` and `recovery/rebuild.log`. Missing Buildx produces a harmless warning; Docker's fallback builder succeeded.
- HTTP smoke checks pass for all six pages, health, greeting, JS/CSS, security header and 404s.
- Original stack checks still pass within the expanded 16-test Chromium suite: greeting updates, Vue counter/remount/history interaction, boosted navigation without reload, titles/current links, overflow checks and keyboard skip link. See portfolio verification above.
- Fixed Vite library-mode output referencing Node's `process` in browser JavaScript. Updated Vite to 7.3.6; frontend npm audit reports zero vulnerabilities. Python dependency security review remains pending.
- Business name, service area, service experience, call/text links, portfolio and the written site content are populated; the stack demo and about placeholder were replaced (see above). Repository-local Git identity is `Project Assistant <project-assistant@localhost>` because none was configured; no global identity or remote added.

## Recovery history (before successful resume)

- Original project lived at `/opt/contractor-site`; moved intact to `/root/dev/contractor-site`.
- All 12 source files written in the previous session matched the log exactly. The generated npm lockfile also survived (13 recovered files total).
- FastAPI routes: `/`, `/services`, `/about`, `/portfolio`, `/before-after`, `/contact`, `/hello`, `/healthz`.
- Placeholder pages, responsive CSS, HTMX greeting/navigation, and a Vue hello counter exist. Contact submissions and photo ingestion do not.
- Multi-stage Dockerfile builds frontend assets, then serves via a non-root Python process. Compose provides Caddy and persistent Caddy volumes.
- Docker and Compose were installed. The first build started but its log ends during dependency installation; no successful build/start or browser tests were recorded. No containers were present at recovery.
- Recovery checks passed: exact source comparison, Python syntax parsing, and `docker compose config --quiet`. **Runtime/build correctness is not yet verified.** Subsequent kernel-log inspection confirmed a global out-of-memory kill of `pi` (PID 10984) at 18:25:19 UTC, followed by kills of several services and `docker-compose` at 18:27:50 UTC. The host has only 453 MiB usable RAM and no swap. Raw evidence is saved in ignored `recovery/oom-kernel.log`. Increase memory, add swap as a safety net, or move builds off-host before retrying the build; no host configuration was changed during diagnosis.
- No prior Git history was found. Local history begins with recovery, not the original development steps.

## Layout

```text
app/main.py             FastAPI routes, page copy and the services list
app/templates/          Jinja layout plus home/services/about/contact/gallery sections
frontend/               HTMX entrypoint, gallery viewer/CSS, site stylesheet, Vite config
app/data/portfolio.json Editable captions, categories, stages, photo provenance/sequences
content/photos/         Original curated JPEG sources (tracked, not served)
content/portraits/      Original About-page portrait source (tracked, not served)
scripts/build_photos.py Reproducible metadata-free WebP generation in Docker
tests/                  HTTP, asset and desktop/mobile browser checks
Dockerfile              Node asset build + Python runtime
compose.yaml            App and Caddy services
Caddyfile               Reverse proxy and response headers
MISSION.md              Copyable continuation prompt
AGENTS.md               Project working and handoff rules
recovery/               Local-only raw session and interrupted build log
```

Raw recovery evidence is deliberately ignored by Git and Docker to avoid publishing session metadata. The original session log remains in `/root/.pi/agent/sessions/--root--/`. Host-installed Docker packages/cache are infrastructure, not project files, and were not moved.

## Run / resume

Requires Docker Engine with Compose v2. Run commands from this project directory:

```sh
cd ~/dev/contractor-site
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 app caddy
curl -fsS http://localhost/healthz
curl -fsS http://localhost/
```

The build needs network access to fetch images and dependencies; the intended deployed site's browser assets are local, not CDN-hosted. Default Caddy binding is HTTP port 80; Compose also reserves 443 TCP/UDP. Starting it exposes the preview on host interfaces, subject to host/cloud firewall rules.

For a real domain, configure `SITE_ADDRESS=example.com` in an untracked `.env`, point DNS at the host, and allow ports 80/443. Confirm HTTPS behavior before production use.

```sh
docker compose down  # stop; preserves named volumes
```

Avoid `down -v` unless intentionally deleting Caddy state/certificates. Local Python startup requires frontend and photo assets first: `cd frontend && npm ci && npm run build` (Node 22 recommended), plus `python scripts/build_photos.py` from the project root in a Python environment with Pillow 11.3.0. Docker handles both automatically and is the verified deployment path. `app/static` and `app/media` are generated and not tracked.

## Repeatable verification

From the project root, with Compose running:

```sh
python3 tests/smoke.py  # optional argument: http://other-host
python3 tests/portfolio_http.py  # checks all images, hashes and source isolation
cd tests/browser
npm ci
PLAYWRIGHT_BROWSERS_PATH=../../recovery/browsers npx playwright install chromium
# On a fresh Linux host, install browser system libraries (requires root):
npx playwright install-deps chromium
npm test
```

Browser tests use one worker to limit memory. All three suites default to `https://ivanpineda.bottah.dev`; pass a base URL argument to the Python checks, or `BASE_URL=http://localhost npm test`, to target a local HTTP-only preview instead. Dependencies, browsers, traces and screenshots are ignored, not committed. Host Node 22 and Python 3 are needed for these tests; app builds require only Docker/Compose.

## Next steps

1. Have the owner confirm the copy listed under “Copy awaiting owner confirmation,” the portrait's authorization, photo captions, stage labels and the three inferred sequences, and the surname spelling.
2. Verify the public site from a browser on another network. Let's Encrypt completed a `tls-alpn-01` challenge for this hostname, so port 443 was reachable from the internet at that moment; that is not the same as a verified visit, and port 80's external reachability is untested.
3. Confirm server-rendered vs truly static requirements (see the architecture clarification). A contact form is not implemented; call/text links are available. Ask before adding a public email.
4. Expand browser/accessibility coverage as real interactions are added; real-device and Safari testing is still missing.
5. Review Python dependency security and deployment readiness before public production use. Add GitHub/CI/CD only when requested.
6. Arrange an off-host backup or remote when authorized; local Git does not survive loss of the droplet.

## Resumability

Start future sessions in this directory. Read `AGENTS.md`, this README, and `git log` before editing. Keep source/config/docs in the project and checkpoint coherent changes with test results and remaining blockers. Local Git cannot survive loss of the droplet by itself: arrange an off-host backup or remote repository when authorized; include ignored recovery evidence separately if wanted.
