# 4. Four visible navigation links, nothing hidden

Status: accepted

## Context

The site has six pages. A first attempt rendered all six as a responsive grid of pill
buttons, which the owner read as dated, and which cost 280px of vertical space on a phone
before any content appeared.

Research was unambiguous. NN/G finds that hiding navigation roughly halves discoverability
and lengthens task time, and that four or fewer top-level links should simply be shown.
The fashionable alternatives fit badly: a floating pill nav holds about four links before
it stops reading as a pill, repaints on every scroll frame through `backdrop-filter`, and
floats over the photographs; a bottom tab bar is for three to five app-like destinations.

## Decision

Reduce the links rather than dress them up. The header carries four — What I do, My work,
About, Contact — as plain text with no container.

- The logo is the home link, so "Home" is not a separate item.
- `/portfolio` and `/before-after` share "My work," which takes `aria-current="true"` on
  both. Those pages carry their own tabs, styled as buttons so they read as a page control
  rather than a second navigation.
- The footer lists every page, NN/G's recommended backstop.
- The current page is marked by the text's own underline in brand gold. That underline is
  the only brand colour in the chrome.

## Consequences

- Four links hold one row at every width down to 320px; the mobile header dropped from
  280px to 168px.
- The header becomes a single line at 860px, measured rather than guessed: brand 413px +
  32px gap + nav 332px + 48px padding = 825px.
- Adding a fifth top-level page breaks the one-row property and forces this decision to be
  revisited — which is the point.
- `tests/browser/site.spec.js` asserts the single row including a 320px check, the four
  labels, the shared section link, and the six footer links.
