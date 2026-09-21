# Architecture decision records

Short records of the choices that are not obvious from reading the code, and would
otherwise be re-litigated or accidentally undone.

| # | Decision |
| --- | --- |
| [0001](0001-server-rendered-not-spa.md) | Server-rendered FastAPI + HTMX, not a static SPA |
| [0002](0002-photo-pipeline.md) | Originals tracked and hash-verified; derivatives generated |
| [0003](0003-licensing-constraint.md) | Unlicensed-contractor constraint, enforced by tests |
| [0004](0004-four-link-navigation.md) | Four visible links, nothing hidden |
| [0005](0005-scroll-snap-carousel.md) | Scroll-snap carousel rather than the native CSS one |
| [0006](0006-asset-cache-versioning.md) | Content-versioned asset URLs and cache headers |
| [0007](0007-no-published-rates.md) | No prices on the site |
| [0008](0008-deployment.md) | Docker Compose + Caddy on a single droplet |
| [0009](0009-brand-assets.md) | Brand artwork processed at build time |
| [0010](0010-continuous-deployment.md) | Push to main deploys over SSH, building on the droplet |
| [0011](0011-dependency-hygiene.md) | Dependencies audited weekly and pinned exactly |
| [0012](0012-preview-deployment.md) | Preview deploys use trusted policy and a runner-built image |
| [0013](0013-production-runtime-limits.md) | Production containers bounded, never tighter than preview |
| [0014](0014-compose-project-isolation.md) | The Compose project name is an isolation boundary |

Format: context, decision, consequences. Keep them short; if one needs reversing, add a
new record that supersedes it rather than rewriting history.
