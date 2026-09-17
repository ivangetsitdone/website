"""Dependency-free HTTP checks against the running Caddy preview."""
import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

base = (sys.argv[1] if len(sys.argv) > 1 else 'https://ivanpineda.bottah.dev').rstrip('/')
SITE = 'https://ivanpineda.bottah.dev'

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
for path, label, heading in [('/', 'Home', 'A helping hand for your home.'),
                             ('/services', 'Services', 'What can I help you with?'),
                             ('/about', 'About', 'Hi, I’m Ivan Pineda.'),
                             ('/portfolio', 'Portfolio', 'Work worth sharing.'),
                             ('/before-after', 'Before &amp; after', 'See the difference.'),
                             ('/contact', 'Contact me', 'Tell me about your project.')]:
    body, _ = fetch(path)
    assert f'>{heading}</h1>' in body, path
    assert f'<title>{label} · Zip LLC Handyman Services</title>' in body, path
    assert f'<link rel="canonical" href="{SITE}{path}">' in body, path
    assert '<meta name="description" content="' in body
    assert '/static/site.js' in body and '/static/site.css' in body
    # Every page offers the confirmed phone contact in the footer.
    assert 'href="tel:+19712883488"' in body and 'href="sms:+19712883488"' in body, path
    # The replaced Hello World stack demo must not reappear.
    assert 'data-vue-hello' not in body and 'hx-get="/hello"' not in body, path
    if path in ('/', '/services', '/contact'):
        assert 'Forest Grove' in body and '30-mile radius' in body, path
    if path in ('/', '/about', '/contact'):
        assert 'evening' in body.lower() and 'weekend' in body.lower(), path

home = fetch('/')[0]
assert 'Call 971-288-3488' in home and 'Text 971-288-3488' in home
assert '/media/p12-full.webp' in home
services = fetch('/services')[0]
for service in ('flooring', 'Shower remodels', 'Interior and exterior painting', 'Fencing',
                'Landscaping', 'Basic plumbing fixture replacement', 'basic electrical work'):
    assert service in services, service
# Scope is presented as experience, not a licensing or suitability promise.
assert 'permits or a licensed specialist' in services
about = fetch('/about')[0]
assert '/media/ivan-pineda.webp' in about and 'Ivan Pineda' in about
contact = fetch('/contact')[0]
assert 'Call 971-288-3488' in contact and 'Text 971-288-3488' in contact
assert 'no online form' in contact
for path, mime in [('/static/site.js', 'javascript'), ('/static/site.css', 'text/css')]:
    body, headers = fetch(path)
    assert body and mime in headers['Content-Type']
# The Hello World demonstration fragment was removed with the stack demo.
fetch('/hello', 404)
fetch('/not-a-page', 404)
fetch('/static/not-a-file', 404)
print('HTTP smoke checks passed.')
