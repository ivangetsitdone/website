# 5. The photo viewer is a scroll-snap carousel, not the native CSS one

Status: accepted

## Context

The viewer swapped `src` on a single `<img>`, so there was nothing to swipe: on a phone the
only way through a project was tapping Previous and Next. CSS Overflow 5 now specifies
`::scroll-button()` and `::scroll-marker`, which build a fully accessible carousel with no
JavaScript — the browser supplies tablist/tab semantics, roving focus and auto-disabled
buttons.

## Decision

Build the track with scroll snapping, which works everywhere, and drive the dots, buttons
and captions with the existing JavaScript rather than the new pseudo-elements.

One slide per photo in a horizontal scroller with `scroll-snap-type: x mandatory` and
`scroll-snap-stop: always`, so swiping is the browser's own scrolling and the buttons, dots
and arrow keys all move the same scroll position.

## Consequences

- `::scroll-button()` and `::scroll-marker` are Chrome/Edge 135+ only; MDN labels them
  "limited availability" and "experimental," with Safari and Firefox unsupported. This
  site's visitors are mostly on mobile Safari, where the dots and arrows would not exist.
  When support arrives, the JS can be replaced by a `@supports` block and deleted — the
  snap track underneath is identical either way.
- Opening a photo inside a project scopes the carousel to that project rather than all
  twenty photos on the page.
- Only the current slide and its two neighbours get a `src`, so opening the 38-photo
  gallery fetches three full images rather than thirty-eight.
- An `IntersectionObserver` syncs caption, counter and dots when the user scrolls; a
  `settling` counter suppresses it while the carousel scrolls itself, so the two never
  fight.
- Axe caught a real defect during this work: a scrollable region with no focusable content
  fails `scrollable-region-focusable`, so the track carries `tabindex="0"`, `role="group"`
  and a label.
