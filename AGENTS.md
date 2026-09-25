# Project working rules

- Treat this directory as the project root; run project commands here. Do not scatter project files in `/root`, `/opt`, or `/tmp`.
- Start by reading README.md, MISSION.md, `git status`, and recent Git history. Preserve existing work.
- Keep source, tests, deployment configuration, and durable decisions in the repository. Document necessary host-level changes and reconstruction steps.
- Use ignored `recovery/` for diagnostic logs and raw session evidence. Never commit secrets, raw session logs, dependencies, or generated assets.
- Distinguish configuration/syntax checks from build, runtime, and browser verification.
- `blog/` holds build-in-public write-ups; `blog/README.md` has the naming and the shape.
  Every number in a post must come from a command that can be re-run.
- Keep README.md as onboarding, not a changelog: durable decisions belong in `docs/adr/`, live action items in `docs/open-questions.md`. Do not invent test results.
- The remote is `github.com/ivangetsitdone/website` and the site deploys from it. Every push to
  `main` is tested on a runner and then deployed via `.github/workflows/deploy.yml`, so treat
  `main` as production; pull requests run the same tests without deploying.
  The droplet's checkout is reset on each deploy; never keep work only on the host.
- **The development site is `/srv/website-dev`, live at <https://dev.ivangetsitdone.com>.**
  A template, `app/main.py`, `app/data` or `app/print` edit there is on that URL within
  seconds, with no commit — it is the place to look at work in progress, and the place to
  show it to someone else. `app/static`, `app/media` and anything under `frontend/` are not
  live there: they come from the image, so they appear after a deploy. The tree is shared, so
  stage files by name rather than `git add -A`. See
  [ADR-0017](docs/adr/0017-development-site-on-one-host.md).
- On the droplet, the live site and a development clone share one Docker daemon. `compose.yaml`
  names its project `website-local` so a clone cannot act on the live containers, which run as
  `website`. Do not add `COMPOSE_PROJECT_NAME=website` to a working clone's `.env`, and do not
  "fix" the `name:` line: it is the only thing standing between `docker compose down -v` in a
  checkout and the live site's TLS certificate.
