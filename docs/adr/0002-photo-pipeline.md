# 2. Photo originals are tracked and hash-verified; derivatives are generated

Status: accepted

## Context

The site is mostly photographs of real jobs, supplied by the owner. They need to be
served small, fast and without EXIF (which carries GPS and device details), while the
originals must stay recoverable and their provenance auditable. Generated files in Git
produce noisy diffs and drift from their sources.

## Decision

Track the original JPEGs in `content/`, never serve them, and record a SHA-256 for each in
`app/data/portfolio.json`. A Docker build stage runs `scripts/build_photos.py`, which
verifies every hash before generating metadata-free WebP derivatives into `app/media/`.
`app/media/` and `app/static/` are git-ignored.

Captions, categories, stages and project groupings live in the same JSON file, editable by
hand.

## Consequences

- **A changed or missing original fails the build.** That tripwire is deliberate: it is how
  a swapped business card or a corrupted photo gets caught rather than silently shipped.
- Pillow never touches the host — it exists only inside a disposable build stage.
- The runtime image contains no original JPEGs, and `tests/portfolio_http.py` asserts that
  `/content/...` paths 404 in production.
- Re-running the one-time importer over the catalogue would overwrite editorial edits, so
  don't; edit the JSON directly.
- The current 38 sources produce 76 project derivatives plus portrait, logo, icon and card —
  about 9.86 MiB served.
