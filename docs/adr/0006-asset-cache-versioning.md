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
- A global `img { max-width: 100% }` rule is the belt-and-braces guard for the day a
  stylesheet does go stale anyway.
