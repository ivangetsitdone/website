# 9. Brand artwork is processed at build time, not by hand

Status: accepted

## Context

The owner supplied a logo and a business card as flat PNGs. The logo is a circular badge on
an opaque white square, and it carries an inner tagline that is illegible at the 52px the
header uses. Hand-editing them in an image editor would leave the result unreproducible and
the provenance unrecorded.

## Decision

Track the originals in `content/brand/` with SHA-256 hashes in the same catalogue as the
photos, and do all processing in `scripts/build_photos.py`.

The build paints out the illegible tagline with the badge colour, measures the non-white
bounding box, checks it is square within 2%, and masks it with a supersampled ellipse — so
`/media/logo.webp` and `/media/logo.png` are transparent and sit cleanly on the page.

## Consequences

- The fill that covers the tagline is bounded per row by the gold perimeter ring, not by a
  fixed rectangle: the badge narrows towards the bottom, and a straight-sided box clipped
  the ring on the lower rows. The band, inset and fill colour are recorded as
  `caption_band` in the catalogue.
- The ring search ignores the middle of the badge so the gold check mark in the wordmark
  cannot be mistaken for the perimeter.
- Replacing the business card is: swap the file, update `sha256` and `alt`, rebuild. The
  hash mismatch is the tripwire that makes a forgotten update loud.
- The palette is drawn from the logo — deep maroon `#5a0000`, athletic gold `#ffd800` — and
  lives as CSS custom properties at the top of `frontend/style.css`. Gold is reserved for
  the current-page underline and focus rings; chrome stays warm-neutral so photographs
  dominate.
