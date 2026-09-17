# Continuation prompt

Resume the contractor services website in `~/dev/contractor-site`. Work only within this project directory for project artifacts. First read `AGENTS.md`, `README.md`, and local Git history; inspect the recovered code rather than starting over.

The mission is a portable, mobile-first contractor website: home, services, about, contact, project photo portfolio, and before/after comparisons. Use FastAPI + Jinja server rendering, HTMX for navigation and partial updates, Vue 3 single-file components only where needed, locally bundled browser assets, Docker Compose, and Caddy. The original “static SPA” wording conflicts with server rendering: confirm whether self-contained assets with SPA-like navigation is sufficient; do not promise a purely static/offline site without resolving that.

The previous session wrote the scaffold but stopped during its first Docker build. Complete and verify the Hello World stack before adding business content. Test HTTP routes, local assets, HTMX interactions/history, Vue behavior, and mobile/keyboard usability. Record what actually passes and any blockers. Ask for business copy, domain, contact destination, and authorized social-media/photo sources before implementing those integrations.

Keep source, configuration, tests, and handoff notes in this repository; keep secrets, raw logs, generated assets, and dependencies out of Git. Make coherent local Git checkpoints and update the README with current status, exact run/test commands, and next steps before ending the session. Do not create a GitHub repository or CI/CD until requested. Document any unavoidable host-level changes. Never treat a started build as a verified deployment.
