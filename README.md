# Contractor Site

A mobile-first contractor services website, recovered from an interrupted development session on 2026-09-17.

## Mission

First prove a working **Hello World** stack: FastAPI + Jinja server rendering, HTMX navigation/partial updates, Vue 3 single-file components only where useful, and locally bundled assets. Package it with Docker Compose and Caddy. Then iterate on services, about, contact, portfolio, and before/after pages using real business details and authorized photos.

**Architecture clarification:** the original request also said “static completely self contained SPA.” The previous assistant interpreted this as self-contained assets and SPA-like navigation, not a purely static/offline application. FastAPI server rendering requires a server. Confirm this interpretation before expanding scope.

No GitHub repository or CI/CD yet; local Git checkpoints are for recovery.

## Verified runtime — 2026-09-17

- Droplet upgraded by owner to 2 GB (1.9 GiB visible); no swap. No host configuration changes made during resume.
- `docker compose config --quiet` and `docker compose up -d --build` passed. App is healthy and Caddy is running; `curl -fsS http://localhost/healthz` returns `{"status":"ok"}`.
- Preview listens on host port 80: `http://<droplet-ip>/` (external firewall/reachability not yet tested). No domain or HTTPS verified.
- Build log: ignored `recovery/resume-build.log`. Build reports one high npm advisory; investigate before production. Missing Buildx produces a harmless warning; Docker's fallback builder succeeded.
- Browser and comprehensive HTTP checks are next. Business content remains placeholder.

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
app/main.py             FastAPI routes and placeholder page data
app/templates/          Jinja pages and greeting fragment
frontend/               Vue SFC, HTMX entrypoint, CSS, Vite config and npm lock
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

Avoid `down -v` unless intentionally deleting Caddy state/certificates. Local Python startup requires frontend assets first: `cd frontend && npm ci && npm run build` (Node 22 recommended); Docker handles this automatically. `app/static` is generated and not tracked.

## Next steps

1. Complete the Docker build and investigate any errors; keep logs inside ignored `recovery/`.
2. Verify all pages, unknown-route 404, `/healthz`, `/hello`, and local JS/CSS through Caddy.
3. Browser-test HTMX navigation/history, Vue mount/unmount, mobile layout, and keyboard access. Add repeatable smoke tests.
4. Confirm server-rendered vs truly static requirements. Obtain business name, service area, services, contact details, domain, and photo-source permissions.
5. Implement real content, gallery/before-after interactions, and a properly handled contact form. Do not imply placeholder forms deliver messages.
6. Review dependency/security updates and deployment readiness before public production use. Add GitHub/CI/CD only when requested.

## Resumability

Start future sessions in this directory. Read `AGENTS.md`, this README, and `git log` before editing. Keep source/config/docs in the project and checkpoint coherent changes with test results and remaining blockers. Local Git cannot survive loss of the droplet by itself: arrange an off-host backup or remote repository when authorized; include ignored recovery evidence separately if wanted.
