# Portfolio source material

The owner uploaded 54 JPEGs and authorized a portfolio with captions and inferred before/after groupings in the project conversation. The supplied attribution is Ivan; the conversation contains both “Pineda” and “Pidena,” so confirm surname spelling before adding a personal credit. Public credit currently uses the confirmed business name, Zip LLC Handyman Services.

35 source photos are preserved unchanged in `photos/` and local Git for reconstruction. These are original source material, not generated website assets. None of the imported JPEGs had EXIF metadata. Original upload filenames and SHA-256 checksums are recorded in `app/data/portfolio.json`; that file is the editable catalog used by the site. Unselected uploads remain in ignored `recovery/uploads/` and are not needed to rebuild.

## Editorial approach

- Captions describe visible features, not verified materials, compliance, dates, locations, or unseen work.
- “Detail” means a project view whose overall completion status is unknown. It does not mean finished.
- All stage labels and sequences are provisional visual interpretations awaiting the owner's review.
- The side-yard pair has matching deck, dish, fence and neighboring wall.
- The steps pair has matching gate and planting; the first shot is already in progress.
- The shower sequence has matching niches/tub corner; even the later image is **in progress**, not a finished installation.
- Parking lot images and sidewalk images are not presented as confirmed before/after pairs.
- Similar angles, blurry excavation close-ups and street scenery were omitted from the first curated selection. This is curation, not deletion of uploads.

## Owner portrait

`portraits/ivan-pineda.jpg` (450×800, JFIF only, no EXIF) is the headshot shown on the About page. It is byte-identical to `recovery/ivan-headshot-download.jpeg`, a file downloaded during the previous session, and the surviving notes do not record who authorized republishing it — the main README still describes the supplied Nextdoor profile as “not fetched or republished.” **Confirm with the owner that this photo may be published before promoting the site.** Its SHA-256 is in `app/data/portfolio.json` under `portrait`; the build stage produces one metadata-free `/media/ivan-pineda.webp` (max 900×900, no upscaling). To pull it, remove the `<figure class="portrait">` block from `app/templates/about.html` together with the portrait steps in `scripts/build_photos.py` and `tests/portfolio_http.py`.

## Rebuild

`docker compose up -d --build` runs `scripts/build_photos.py` in a Pillow-only build stage. It validates source hashes and generates two metadata-free WebP versions per photo (thumbnail up to 480×640; viewer up to 1440×1440, no upscaling). Only those derivatives go into the runtime container at `/srv/app/media`; original source photos are not served or copied into the final image.

Generated images live under ignored `app/media/` when built locally. `scripts/curate_photos.py` records the one-time selection/import from the initial 54 uploads; don't rerun it over subsequent caption edits. Edit the catalog directly for editorial changes. For new images, add source JPEGs with unique IDs and checksums to the catalog, then rebuild and test.

All preservation is local until an off-host backup or remote is authorized. Keep the MacBook originals too.
