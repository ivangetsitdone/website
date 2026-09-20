# Blog

Build-in-public write-ups from this repository. Each one takes a single problem that
actually happened here, and follows it from the symptom to the fix, with the measurements
that justified each step.

Nothing in this directory ships. The Dockerfile copies `app/`, `frontend/`, `content/`,
`scripts/build_photos.py` and `requirements.txt` — so a post is a no-op deploy that still
runs the full pipeline, which is a pleasant way to test it.

## Posts

| Date | Namespace | Post |
| --- | --- | --- |
| 2026-09-20 | process | [The pull request nobody needed](2026-09-20-process-the-pull-request-nobody-needed.md) — what a pull request actually buys a one-person repo, and what changes when a second person arrives |
| 2026-09-20 | deploy | [Eight seconds of 502](2026-09-20-deploy-eight-seconds-of-502.md) — giving a one-droplet site a real pipeline, and finding three defects in how it had been deploying all along |

## Conventions

**Filename:** `YYYY-MM-DD-<namespace>-<slug>.md`. The date is when it was written, not when
the work happened. The namespace is the part of the stack it belongs to — so far `deploy`,
with `frontend`, `images` and `content` waiting for their turn. If a namespace ever earns
more than a handful of posts, it becomes a directory. Not yet.

**Shape.** Setup, buildup, climax, recap:

- **Setup** — the stack and the constraint. Enough that a stranger can picture the machine.
- **Buildup** — what was tried, in the order it was tried, including the things that did not
  work. The wrong turns are the useful part; a post that only shows the final answer teaches
  nothing about how to find one.
- **Climax** — the moment the real problem became visible. There is usually exactly one, and
  it is usually not where the investigation started.
- **Recap** — what changed, what it measures now, and what a reader can take away without
  having this stack.

**Every number comes from a command that can be re-run.** No estimates dressed as
measurements. If something was not measured, the post says it was not measured. This rule
exists because the first draft of the deploy post confidently said "the gap is seconds" —
it was 8.4 of them, and only saying so out loud got it measured.

**Write about the layer that was just peeled.** The interesting material is never the design
that worked first time; it is the assumption the project had been carrying without noticing.

## Candidates, when they are ready

- **The race no laptop could lose** — `frontend`. A boosted navigation updated the page's
  `<title>` about 20ms before its `<meta name="description">`, and CI on a slower machine
  caught it twice in a row while two local machines never reproduced it once.
- **A catalogue that fails the build** — `images`. 35 originals, a SHA-256 per file in the
  catalogue, and a photo pipeline that refuses to build rather than quietly shipping a
  swapped source.
- **Writing copy against a legal constraint** — `content`. The site advertises for a business
  with no contractor's licence, so the test suite fails if regulated trades appear in the
  blocks that offer work. Tests as an editorial guardrail.
