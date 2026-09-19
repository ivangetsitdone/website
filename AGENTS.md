# Project working rules

- Treat this directory as the project root; run project commands here. Do not scatter project files in `/root`, `/opt`, or `/tmp`.
- Start by reading README.md, MISSION.md, `git status`, and recent Git history. Preserve existing work.
- Keep source, tests, deployment configuration, and durable decisions in the repository. Document necessary host-level changes and reconstruction steps.
- Use ignored `recovery/` for diagnostic logs and raw session evidence. Never commit secrets, raw session logs, dependencies, or generated assets.
- Distinguish configuration/syntax checks from build, runtime, and browser verification.
- Keep README.md as onboarding, not a changelog: durable decisions belong in `docs/adr/`, live action items in `docs/open-questions.md`. Do not invent test results.
- The remote is `github.com/ivangetsitdone/website` and the site deploys from it. CI/CD is still not configured; ask before adding it.
