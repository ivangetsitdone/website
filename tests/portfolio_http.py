"""Check catalog, generated public assets and source isolation through Caddy."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent
base = (sys.argv[1] if len(sys.argv) > 1 else 'https://ivanpineda.bottah.dev').rstrip('/')
catalog = json.loads((ROOT / 'app/data/portfolio.json').read_text())
ids = [photo['id'] for photo in catalog['photos']]
assert len(ids) == len(set(ids))
size = 0
for photo in catalog['photos']:
    source = ROOT / 'content/photos' / (photo['id'] + '.jpg')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == photo['sha256']
    for variant in ('thumb', 'full'):
        path = f"/media/{photo['id']}-{variant}.webp"
        with urlopen(base + path, timeout=10) as response:
            data = response.read()
            assert response.status == 200 and response.headers['Content-Type'] == 'image/webp'
            assert data[:4] == b'RIFF' and data[8:12] == b'WEBP'
            assert len(data) < 500_000, (path, len(data))
            size += len(data)
for pair in catalog['pairs']:
    assert all(key in ids for key in pair['photos'])
portrait = catalog['portrait']
portrait_source = ROOT / 'content/portraits' / (portrait['id'] + '.jpg')
assert hashlib.sha256(portrait_source.read_bytes()).hexdigest() == portrait['sha256']
with urlopen(f"{base}/media/{portrait['id']}.webp", timeout=10) as response:
    data = response.read()
    assert response.status == 200 and response.headers['Content-Type'] == 'image/webp'
    assert data[:4] == b'RIFF' and data[8:12] == b'WEBP'
    assert len(data) < 500_000, len(data)
    size += len(data)
for path in ('/media/missing.webp', '/media/p12.jpg', '/content/photos/p12.jpg',
             '/content/portraits/ivan-pineda.jpg', '/recovery/uploads/', '/data/portfolio.json'):
    try:
        urlopen(base + path, timeout=10)
    except HTTPError as error:
        assert error.code == 404, (path, error.code)
    else:
        raise AssertionError(f'Should not be public: {path}')
print(f'PASS {len(ids)} catalog sources, {len(ids) * 2} project WebP assets plus 1 portrait '
      f'({size / 1024 / 1024:.2f} MiB total), sequences and source isolation.')
