"""Build metadata-free WebP thumbnails and viewer images from curated sources.

Uses Pillow in a disposable Docker build stage; never serves original uploads.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
catalog = json.loads((ROOT / 'app/data/portfolio.json').read_text())
output = ROOT / 'app/media'
output.mkdir(parents=True, exist_ok=True)
ids = set()
for photo in catalog['photos']:
    key = photo['id']
    assert key not in ids and key.startswith('p') and key[1:].isdigit()
    ids.add(key)
    source = ROOT / 'content/photos' / f'{key}.jpg'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == photo['sha256'], source
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert('RGB')
        for label, size, quality in [('thumb', (480, 640), 78), ('full', (1440, 1440), 80)]:
            resized = image.copy()
            resized.thumbnail(size, Image.Resampling.LANCZOS)
            # Copy pixels into a fresh image to discard all source metadata.
            clean = Image.new('RGB', resized.size)
            clean.paste(resized)
            clean.save(output / f'{key}-{label}.webp', 'WEBP', quality=quality, method=6)
for pair in catalog['pairs']:
    assert all(key in ids for key in pair['photos']), pair
print(f'Built {len(ids) * 2} WebP images in {output}')
