"""Dependency-free HTTP checks against the running Caddy preview."""
import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

base = (sys.argv[1] if len(sys.argv) > 1 else 'https://ivanpineda.bottah.dev').rstrip('/')
SITE = 'https://ivanpineda.bottah.dev'
# Ivan holds no Oregon CCB or trade license yet, so the blocks that offer work must
# never name regulated construction. The wording lives only in the "what I don't take
# on" note and in the work-history pages, which describe past experience.
LICENSE_NOTE_OPENING = 'Zip, LLC is not a CCB-licensed contractor.'
REGULATED = ('remodel', 'sheetrock', 'drywall', 'tile', 'flooring', 'plumbing',
             'electrical', 'painting', 'shower', 'install', 'repair', 'retaining wall')

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

def between(body, start, end):
    first = body.index(start)
    return body[first:body.index(end, first)]

assert json.loads(fetch('/healthz')[0]) == {'status': 'ok'}
for path, label, heading in [('/', 'Home', 'Consider it done.'),
                             ('/services', 'What I do', 'Small jobs, done properly.'),
                             ('/about', 'About', 'Hi, I’m Ivan Pineda.'),
                             ('/portfolio', 'My work', 'Work I’ve had a hand in.'),
                             ('/before-after', 'Project stories', 'See the difference.'),
                             ('/contact', 'Contact me', 'Tell me about your project.')]:
    body, _ = fetch(path)
    assert f'>{heading}</h1>' in body, path
    assert f'<title>{label} · Zip, LLC</title>' in body, path
    # The registered entity name carries a comma; copy must match the registry.
    assert 'Zip LLC' not in body, path
    # Advertising as a handyman is contractor advertising in Oregon; the word must not
    # appear in public copy while Ivan is unlicensed.
    assert 'handyman' not in body.lower(), path
    # The owner asked that no specific length of experience be claimed; the registration
    # date carries that weight instead.
    for claim in ('ten years', '10 years', '10+ years', 'years of experience', 'years of hands-on'):
        assert claim not in body.lower(), (path, claim)
    assert f'<link rel="canonical" href="{SITE}{path}">' in body, path
    assert '<meta name="description" content="' in body
    assert '/static/site.js' in body and '/static/site.css' in body
    # Every page offers the confirmed phone contact and carries the licensing disclosure.
    assert 'href="tel:+19712883488"' in body and 'href="sms:+19712883488"' in body, path
    # The licensing fact is said once per page, in the footer, with the registration.
    assert 'Oregon business registry' in body and 'Not a CCB-licensed contractor.' in body, path
    assert '#2249807-97' in body and 'sos.oregon.gov/business/Pages/find.aspx' in body, path
    # htmx must not try to boost an off-site link.
    assert 'hx-boost="false" target="_blank"' in body, path
    # Said once, on the services page. The footer short form covers every other page.
    assert body.count(LICENSE_NOTE_OPENING) == (1 if path == '/services' else 0), path
    assert 'data-vue-hello' not in body and 'hx-get="/hello"' not in body, path
    if path in ('/', '/services', '/contact'):
        assert 'Forest Grove' in body and '30-mile radius' in body, path
    if path in ('/', '/about', '/contact'):
        assert 'evening' in body.lower() and 'weekend' in body.lower(), path

home = fetch('/')[0]
assert 'Call 971-288-3488' in home and 'Text 971-288-3488' in home
assert '/media/p42-full.webp' in home
assert '<time datetime="2024-04-04">April 2024</time>' in home
offered_home = between(home, 'service-preview-grid', 'licence-note')
for word in REGULATED:
    assert word not in offered_home.lower(), ('home offers regulated work', word)

services = fetch('/services')[0]
for service in ('Yard cleanup', 'hauling', 'Pressure washing', 'Gutter clearing', 'Moving'):
    assert service in services, service
offered = between(services, '<section class="services-grid', '<aside class="scope-note"')
for word in REGULATED:
    assert word not in offered.lower(), ('services page offers regulated work', word)
# The regulated trades appear only in the note that declines them.
scope = between(services, '<aside class="scope-note"', '</aside>')
for word in (LICENSE_NOTE_OPENING, 'Oregon CCB exam', 'licensed contractor'):
    assert word in scope, word

about = fetch('/about')[0]
assert '/media/ivan-pineda.webp' in about and 'Ivan Pineda' in about
assert 'Construction Contractors Board exam' in about
for path in ('/portfolio', '/before-after'):
    body = fetch(path)[0]
    # Past work is presented as experience, never as services on offer.
    assert 'my work history rather than the services I offer today' in body, path

contact = fetch('/contact')[0]
assert 'Call 971-288-3488' in contact and 'Text 971-288-3488' in contact
assert 'no online form' in contact
for path, mime in [('/static/site.js', 'javascript'), ('/static/site.css', 'text/css')]:
    body, headers = fetch(path)
    assert body and mime in headers['Content-Type']
fetch('/hello', 404)
fetch('/not-a-page', 404)
fetch('/static/not-a-file', 404)
print('HTTP smoke checks passed.')
