# Portfolio source material

The owner uploaded 54 JPEGs and authorized a portfolio with captions and inferred before/after groupings in the project conversation. The supplied attribution is Ivan; the conversation contains both “Pineda” and “Pidena,” so confirm surname spelling before adding a personal credit. Public credit uses the registered business name, Zip, LLC. The words “handyman services” were removed from public copy on 2026-09-18 for licensing reasons; see the main README.

35 source photos are preserved unchanged in `photos/` and local Git for reconstruction. These are original source material, not generated website assets. None of the imported JPEGs had EXIF metadata. Original upload filenames and SHA-256 checksums are recorded in `app/data/portfolio.json`; that file is the editable catalog used by the site. Unselected uploads remain in ignored `recovery/uploads/` and are not needed to rebuild.

## Editorial approach

- Captions describe visible features, not verified materials, compliance, dates, locations, or unseen work.
- “Detail” means a project view whose overall completion status is unknown. It does not mean finished.
- The owner has confirmed all seven project groupings, so the public notes state them plainly instead of hedging with “Likely.” Stage labels and captions for photos outside those groupings are still visual interpretations awaiting review; keep that caveat here rather than in site copy.
- The side-yard pair has matching deck, dish, fence and neighboring wall.
- Corrected by the owner on 2026-09-18: Ivan **built** the garden steps. The first curation read p42 as an existing path uncovered (“Garden steps revealed”), which was wrong and undersold the work; the captions now describe digging out the old path and setting the new flight. Treat this as the standing example of why inferred captions need owner review.
- The shower project opens with two photos the owner confirmed as **before** shots of the original white tile shower (p15, p16); the rebuild photos that follow have matching niches/tub corner and are still **in progress**, not a finished installation.
- The owner confirmed three further before/after pairs: the leaf-covered sidewalk strip (p43 → p44), the parking lot before and after restriping (p23 → p24), and the siding repair before and after finishing (p09 → p10). The owner also confirmed that p02 and p04 show rotted fence posts being replaced and the fence afterwards. Their stage labels, titles and captions were updated to match.
- Similar angles, blurry excavation close-ups and street scenery were omitted from the first curated selection. This is curation, not deletion of uploads.

## Using these photos

The photo archive is published as Ivan's **work history**, not as an advertisement of services: he holds no Oregon CCB license yet (see the licensing section in the main README). Captions describe the work; nothing on those pages offers to perform it. Before expanding the archive, confirm which projects were his own property or done as an employee, and keep new captions free of any offer to do that work for hire.

## Owner portrait

`portraits/ivan-pineda.jpg` (450×800, JFIF only, no EXIF) is the headshot shown on the About page. It is byte-identical to `recovery/ivan-headshot-download.jpeg`, a file downloaded during the previous session, and the surviving notes do not record who authorized republishing it — the main README still describes the supplied Nextdoor profile as “not fetched or republished.” **Confirm with the owner that this photo may be published before promoting the site.** Its SHA-256 is in `app/data/portfolio.json` under `portrait`; the build stage produces one metadata-free `/media/ivan-pineda.webp` (max 900×900, no upscaling). To pull it, remove the `<figure class="portrait">` block from `app/templates/about.html` together with the portrait steps in `scripts/build_photos.py` and `tests/portfolio_http.py`.

## Brand assets

`brand/logo.png` and `brand/business-card.png` are the owner-supplied originals, tracked with hashes in the catalog and never served directly. The logo arrives as a circle on an opaque white square; the build masks it to a transparent badge. The card was replaced on 2026-09-18 with the owner's new artwork, which prints **IvanGetsItDone.com**. That domain was not registered when the card was swapped (Verisign RDAP returned 404, and the name had no A, NS or SOA records); it was registered and pointed at the site on 2026-09-19, so the printed address and the site now agree.

## Rebuild

`docker compose up -d --build` runs `scripts/build_photos.py` in a Pillow-only build stage. It validates source hashes and generates two metadata-free WebP versions per photo (thumbnail up to 480×640; viewer up to 1440×1440, no upscaling). Only those derivatives go into the runtime container at `/srv/app/media`; original source photos are not served or copied into the final image.

Generated images live under ignored `app/media/` when built locally. `scripts/curate_photos.py` records the one-time selection/import from the initial 54 uploads; don't rerun it over subsequent caption edits. Edit the catalog directly for editorial changes. For new images, add source JPEGs with unique IDs and checksums to the catalog, then rebuild and test.

All preservation is local until an off-host backup or remote is authorized. Keep the MacBook originals too.
