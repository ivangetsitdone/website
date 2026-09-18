"""Build metadata-free WebP thumbnails and viewer images from curated sources.

Uses Pillow in a disposable Docker build stage; never serves original uploads.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageOps

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

portrait = catalog['portrait']
portrait_source = ROOT / 'content/portraits' / f"{portrait['id']}.jpg"
assert hashlib.sha256(portrait_source.read_bytes()).hexdigest() == portrait['sha256'], portrait_source
with Image.open(portrait_source) as original:
    image = ImageOps.exif_transpose(original).convert('RGB')
    image.thumbnail((900, 900), Image.Resampling.LANCZOS)
    clean = Image.new('RGB', image.size)
    clean.paste(image)
    assert clean.size == (portrait['width'], portrait['height']), clean.size
    clean.save(output / f"{portrait['id']}.webp", 'WEBP', quality=82, method=6)

def transparent_badge(image):
    """Trim the flat background from the round logo and give it an alpha channel.

    The supplied artwork is a circular badge on an opaque white square. The white
    margin is measured rather than assumed, and the circle is masked with a
    supersampled ellipse so the edge stays smooth against any page colour.
    """
    rgb = image.convert('RGB')
    background = Image.new('RGB', rgb.size, (255, 255, 255))
    difference = ImageChops.difference(rgb, background).convert('L')
    box = difference.point(lambda value: 255 if value > 24 else 0).getbbox()
    assert box, 'logo appears to be blank'
    art = rgb.crop(box)
    width, height = art.size
    assert abs(width - height) <= max(width, height) * 0.02, ('logo artwork is not square', art.size)
    scale = 4
    mask = Image.new('L', (width * scale, height * scale), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, width * scale - 1, height * scale - 1), fill=255)
    art = art.convert('RGBA')
    art.putalpha(mask.resize((width, height), Image.Resampling.LANCZOS))
    return art


brand = catalog['brand']
logo = None
for key, spec in brand.items():
    source = ROOT / 'content/brand' / spec['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == spec['sha256'], source
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        if key == 'logo':
            logo = transparent_badge(image)
            logo.thumbnail((spec['size'], spec['size']), Image.Resampling.LANCZOS)
            # Copy the pixels into a fresh image so no source metadata survives.
            clean = Image.new('RGBA', logo.size)
            clean.paste(logo)
            clean.save(output / 'logo.webp', 'WEBP', quality=90, method=6, exact=True)
            clean.save(output / 'logo.png', 'PNG', optimize=True)
            icon = clean.copy()
            icon.thumbnail((180, 180), Image.Resampling.LANCZOS)
            icon.save(output / 'icon.png', 'PNG', optimize=True)
        else:
            flat = image.convert('RGB')
            flat.thumbnail((spec['width'], spec['width']), Image.Resampling.LANCZOS)
            clean = Image.new('RGB', flat.size)
            clean.paste(flat)
            clean.save(output / 'card.webp', 'WEBP', quality=88, method=6)

print(f'Built {len(ids) * 2} project WebP images, 1 portrait and {len(brand)} brand assets '
      f'(logo masked to {logo.size[0]}px, transparent) in {output}')
