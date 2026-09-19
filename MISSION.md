# Continuation prompt

Resume the Zip, LLC website in this directory. Read `AGENTS.md`, `README.md` and recent Git
history first, and inspect the code rather than starting over.

The site is live at <https://ivangetsitdone.com>, deployed from
<https://github.com/ivangetsitdone/website> onto a DigitalOcean droplet. It is built and
verified; the work now is refinement, not construction.

**Licensing shapes every copy change.** Ivan has no Oregon CCB licence, so the site
advertises only unregulated work and presents the photo archive as past experience. Read
[ADR-0003](docs/adr/0003-licensing-constraint.md) before editing any public wording — the
test suite fails if regulated trades reappear in the blocks that offer work.

- **Why things are as they are:** `docs/adr/`. Add a record rather than silently reversing one.
- **What still needs a human answer:** `docs/open-questions.md` — owner confirmations,
  questions for the CCB, and the testing gaps (no real-device or Safari coverage).
- **How to run, edit and test:** `README.md`. **How to deploy:** `DEPLOY.md`.

Run the three suites after changes and record what actually passed. Never treat a started
build as a verified deployment. Ask before adding a public email, a contact form, or any
social-media or photo import.
