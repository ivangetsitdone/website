# 3. The site advertises only unregulated work, and tests enforce it

Status: accepted — read before editing any public copy

## Context

Ivan holds an Oregon business registration (Zip, LLC, registry 2249807-97) but **no CCB
contractor licence**, and no electrical or plumbing trade licence. Oregon requires a CCB
licence to advertise construction work, requires licensees to publish their CCB number in
advertising, and conditions the small-job exemption on *not* advertising or holding oneself
out as a contractor. Electrical and plumbing are licensed separately through the Building
Codes Division; fences, decks, patios and retaining walls are typically Landscape
Contractors Board work.

The owner has a decade of hands-on experience and a photo archive that shows it. Throwing
that away would gut the site's credibility; showing it as a service menu would be
advertising unlicensed contracting.

## Decision

Advertise only work that needs none of those licences, and present everything else as
personal history.

- **Offered** (`SERVICES` in `app/main.py`): yard cleanup and leaf removal, junk and debris
  hauling, pressure washing, gutter clearing, moving and assembly help, seasonal odd jobs.
- **The site never lists what Ivan cannot do.** A list of refusals reads as defensive and
  scares off customers. The protection comes from what the offer omits.
- **One disclosure per page**: the footer carries the registered name, the registry number
  linked to the Secretary of State search page, and "Not a CCB-licensed contractor."
- **One forward-looking note**, `LICENSE_NOTE`, appears exactly once on the whole site — on
  the About page, beside the profile, where it reads as part of his story.
- **The photo archive is framed as experience**, with an explicit line that it is "not a
  list of services I'm offering today," and no call to action attached to that work.
- The word "handyman" appears nowhere: in Oregon it reads as contractor advertising.

## Consequences

- `tests/smoke.py` and `tests/browser/site.spec.js` fail if any regulated-trade word
  (remodel, sheetrock, drywall, tile, flooring, plumbing, electrical, painting, shower,
  install, repair, retaining wall) appears inside the blocks that offer work; if the
  disclosure is missing from any page; if `LICENSE_NOTE` appears anywhere but About, or
  more than once; or if "handyman" returns. **Keep those checks.** They are the reason a
  well-meaning copy edit cannot quietly re-advertise construction.
- The printable honey-do list carries the disclosure too, because it leaves the site on
  paper with the business name and number on it.
- Parking-lot striping is treated as regulated painting and sits in the licensed group.
- **When the licence is issued**: the CCB number must appear in advertising. Add it to the
  footer, then remove the disclosure and the "not offering" framing, and relax the
  guardrails deliberately rather than by accident.
- This is not legal advice, and the CCB answers these questions directly. Open items are
  tracked in [docs/open-questions.md](../open-questions.md).
