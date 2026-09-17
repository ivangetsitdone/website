"""Dependency-free HTTP checks against the running Caddy preview."""
import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

base = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost').rstrip('/')

def fetch(path, status=200):
    try:
        response = urlopen(base + path, timeout=10)
    except HTTPError as exc:
        response = exc
    with response:
        assert response.status == status, (path, response.status)
        body = response.read().decode()
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        print(f'PASS {status} {path}')
        return body, response.headers

assert json.loads(fetch('/healthz')[0]) == {'status': 'ok'}
for path, title in [('/', 'Hello World'), ('/services', 'Built around your project.'),
                    ('/about', 'Meet your contractor.'), ('/portfolio', 'Work worth sharing.'),
                    ('/before-after', 'See the difference.'), ('/contact', 'Let’s build something.')]:
    body, _ = fetch(path)
    assert f'<h1>{title}</h1>' in body
    assert '/static/site.js' in body and '/static/site.css' in body
    if path in ('/', '/services'):
        assert 'Forest Grove' in body and '30-mile radius' in body
assert 'UTC' in fetch('/hello')[0]
for path, mime in [('/static/site.js', 'javascript'), ('/static/site.css', 'text/css')]:
    body, headers = fetch(path)
    assert body and mime in headers['Content-Type']
fetch('/not-a-page', 404)
fetch('/static/not-a-file', 404)
print('HTTP smoke checks passed.')
