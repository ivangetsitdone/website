# 6. Content-versioned asset URLs and explicit cache headers

Status: accepted

## Context

Generated assets keep stable filenames across builds, and neither Caddy nor FastAPI was
sending `Cache-Control`. Browsers applied heuristic caching, and the owner saw a stale
stylesheet render the new business card at its full 1400px width.

## Decision

Templates call `asset('/static/site.css')`, which appends a version derived from the file's
size and mtime. A middleware sends `public, max-age=31536000, immutable` for URLs carrying
that version, and `no-cache` for bare asset URLs and for HTML.

## Consequences

- Every generated asset the templates reference must go through `asset()` — gallery
  thumbnails and viewer images included. When they did not, `no-cache` forced a
  revalidation round trip per image and the heaviest browser test began timing out.
- Smoke checks assert both headers and the `?v=` markers.
- **The version is recomputed on every call, never memoised.** It was cached for the life
  of the process until the development site of [ADR-0017](0017-development-site-on-one-host.md)
  made that unsafe: a cached version outliving the bytes it describes is a year-long
  `immutable` promise about the wrong file, which no browser will revalidate, not even on a
  manual reload. Measured at 4.06 us per reference, about 309 us for the gallery page's 76;
  memoising the digest recovers 38 us of that, because the dict lookup costs about what the
  hash does. `app/assets.py` holds the helper, with no web-framework import so the check job
  can test it before the stack exists, and `tests/test_asset_versions.py` asserts both the
  behaviour and the absence of a cache.
- A global `img { max-width: 100% }` rule is the belt-and-braces guard for the day a
  stylesheet does go stale anyway.
