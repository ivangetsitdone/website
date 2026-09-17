# Project working rules

- Treat this directory as the project root; run project commands here. Do not scatter project files in `/root`, `/opt`, or `/tmp`.
- Start by reading README.md, MISSION.md, `git status`, and recent Git history. Preserve existing work.
- Keep source, tests, deployment configuration, and durable decisions in the repository. Document necessary host-level changes and reconstruction steps.
- Use ignored `recovery/` for diagnostic logs and raw session evidence. Never commit secrets, raw session logs, dependencies, or generated assets.
- Establish the Hello World stack before expanding features. Distinguish configuration/syntax checks from build, runtime, and browser verification.
- Before handoff, update README.md with verified state, commands, blockers, and next steps; create a coherent local Git checkpoint. Do not invent test results.
- Do not create remotes, publish to GitHub, or configure CI/CD without approval. Local Git is not an off-host backup.
