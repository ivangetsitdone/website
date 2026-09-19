# 7. No prices on the site

Status: accepted

## Context

The owner drafted a panel for the services page that explained pricing plainly: an hourly
rate, a minimum visit charge, materials extra, shopping time billed. He then decided the
figures belong in a conversation rather than on a web page, where they invite comparison
shopping and go stale.

## Decision

Keep the panel and its promise — "A small job shouldn't come with a big mystery" — but
describe *how* the work is charged rather than what it costs, and send people to call or
text for the numbers. No figure appears anywhere on the site.

## Consequences

- `tests/smoke.py` and `tests/browser/site.spec.js` both fail if a `$` appears inside that
  panel. If a rate is ever meant to be published, that check is what to change — on
  purpose, not by accident.
- The panel still commits to the behaviour that matters: explain the expected cost before
  starting, and check in before exceeding what was agreed.
