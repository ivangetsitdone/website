# Open questions

Live items, not history. Each needs a person outside this repository to answer.

## For the owner

**Copy that is live but never confirmed.** These came from an early session whose context
was lost. They are plausible and consistent, but nothing in this repository records the
owner agreeing to them.

- Availability limited to evenings and weekends around a full-time job.
- The personal note about supporting his family and saving for his daughter's college fund.
- The surname spelling **Pineda**, used in copy, the footer and the domain. `content/README.md`
  records a Pineda/Pidena ambiguity that was never resolved.
- **Publishing the About-page portrait.** Its authorization is not recorded anywhere. The
  repository is public, so the original file is published as a file regardless of the page.

**Wording that is mine, not the owner's.**

- "Contact" in the header navigation, where the page itself is titled "Contact me".
- "All photos" as the first work-section tab.

**Photo captions and stage labels.** The seven project groupings are owner-confirmed. The
captions on individual photos outside those groupings are inferred from what is visible and
deserve a read-through. The garden-steps entry is the cautionary example: it originally read
as though Ivan had uncovered an existing flight of steps, when he had built them — back-
breaking work described as sweeping up.

## For the CCB

None of this is legal advice, and the CCB answers these directly. Background is in
[ADR-0003](adr/0003-licensing-constraint.md).

1. **Have the CCB review the live pages.** A site showing remodelling photographs beside a
   phone number could still be read as holding out, even framed as experience and carrying
   the disclosure.
2. **Which archived jobs were paid work performed unlicensed?** Work on his own property, or
   done as an employee, is a different matter from a paid unlicensed job. Worth knowing
   before displaying them.
3. **Do pressure washing, gutter clearing and hauling sit outside CCB and LCB jurisdiction**
   as actually performed?
4. **The tagline.** "Honey Dos · Hauling · Yard Care · Small Projects" is the owner's
   wording. "Small Projects" and "Honey Dos" read as classic handyman advertising, which is
   the phrasing the exemption is conditioned against, and both are broader than the six
   services actually offered. A self-limiting alternative — "Residential Yard Care ·
   Hauling · Cleaning" — was the prior wording and is a one-line revert.
5. **The registered business name.** If the entity is registered as "Zip LLC Handyman
   Services", that registration is separate from this site; ask whether it needs amending.
   The site itself says "Zip, LLC" and the word "handyman" appears nowhere.

## Technical, unfinished

- **No real-device or Safari testing has ever been done.** Everything verified here is
  Chromium at two viewport sizes. The carousel, which leans on scroll snapping and an
  `IntersectionObserver`, is the most likely thing to behave differently on iOS.
- **Dependency security is audited weekly.** `pip-audit` and `npm audit` run on a schedule
  (`.github/workflows/audit.yml`), and Dependabot opens update PRs. The one finding so far
  was a starlette DoS, fixed in the starlette 1.6.0 pin; see [ADR-0011](adr/0011-dependency-hygiene.md).
- **The site has not been opened from another network.** Let's Encrypt completed a
  challenge, so port 443 was reachable from the internet at that moment; that is not the
  same as a human visiting successfully.
- **No public email address**, by choice — calls and texts only, and there is no contact
  form. Ask before adding either.
- **Nothing imports from Nextdoor.** A profile URL was supplied but never fetched or
  republished.
