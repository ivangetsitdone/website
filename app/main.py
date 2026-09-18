import json
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).parent
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
app.mount('/media', StaticFiles(directory=ROOT / 'media'), name='media')
templates = Jinja2Templates(directory=ROOT / 'templates')
PORTFOLIO = json.loads((ROOT / 'data/portfolio.json').read_text())
PHOTOS = PORTFOLIO['photos']
PHOTO_BY_ID = {photo['id']: photo for photo in PHOTOS}
CATEGORIES = list(dict.fromkeys(photo['category'] for photo in PHOTOS))
PAIRS = [{**pair, 'photos': [PHOTO_BY_ID[key] for key in pair['photos']]}
         for pair in PORTFOLIO['pairs']]
PORTRAIT = PORTFOLIO['portrait']
HERO = PHOTO_BY_ID['p42']
PAGES = {
    '': ('Home', 'Consider it done.', 'I’m Ivan Pineda. Evenings and weekends I work through the honey-do list: yard cleanups, junk hauling, pressure washing, gutters and moving help around Forest Grove and within a 30-mile radius.'),
    'services': ('What I do', 'Small jobs, done properly.', 'Yard cleanups, debris hauling, pressure washing, gutter clearing and moving help in Forest Grove and the surrounding communities. Construction, plumbing and electrical work needs a licensed contractor, and I am studying for that license now.'),
    'about': ('About', 'Hi, I’m Ivan Pineda.', 'A hardworking local with a lifetime of hands-on building experience, working toward an Oregon CCB license while taking on the smaller jobs around the home.'),
    'portfolio': ('My work', 'Work I’ve had a hand in.', 'A record of projects I have worked on: showers, flooring, fences, painting and outdoor work. This is my work history, not a list of services I am offering today.'),
    'before-after': ('Project stories', 'See the difference.', 'A closer look at projects I have worked on, photographed before, during and after. Part of my work history rather than services on offer.'),
    'contact': ('Contact me', 'Tell me about your project.', 'Call or text me at 971-288-3488 about yard, hauling, cleaning or moving work. Serving Forest Grove and surrounding communities within a 30-mile radius, evenings and weekends.'),
}
SERVICES = [
    ('Yard cleanup & leaf removal', 'Overgrown corners, leaf fall, brush and weeds cleared out, with the debris hauled away.'),
    ('Junk & debris hauling', 'Garage, shed and yard clear-outs, loaded up and taken to the transfer station.'),
    ('Pressure washing', 'Driveways, sidewalks, patios, siding and fences washed down and brightened up.'),
    ('Gutter clearing', 'Gutters and downspouts cleared of leaves and grit before the wet season sets in.'),
    ('Moving & assembly help', 'An extra pair of hands for loading, moving furniture around the house and putting flat-pack furniture together.'),
    ('Seasonal odd jobs', 'The small maintenance jobs on your list. If you are not sure whether it is something I can take on, just ask.'),
]
# Work that needs an Oregon CCB or trade license. Named here so visitors are pointed
# to a licensed contractor, never offered as a service.
NOT_OFFERED = [
    'Remodeling, tile, flooring and sheetrock',
    'Painting of any kind — interior, exterior or pavement marking',
    'Fences, decks, patios and retaining walls',
    'Plumbing and electrical work of any kind',
]
DISCLOSURE = ('Zip, LLC is not licensed by the Oregon Construction Contractors Board. '
              'I take on yard, hauling, cleaning and moving work only. Construction, plumbing and '
              'electrical work needs a licensed contractor.')
# Said once per page in the footer; the full disclosure lives on the services page.
SHORT_DISCLOSURE = 'Not a CCB-licensed contractor.'
# The owner's Oregon Secretary of State registration. The direct record URL on
# egov.sos.state.or.us sits behind bot protection that can show visitors an error page,
# so the public link points at the stable search page and the number is given in text.
REGISTRY = {
    'name': 'Zip, LLC',
    'number': '2249807-97',
    'registered': '2024-04-04',
    'registered_label': 'April 2024',
    'search_url': 'https://sos.oregon.gov/business/Pages/find.aspx',
}

@app.get('/healthz')
def health():
    return {'status': 'ok'}


@app.get('/', response_class=HTMLResponse)
@app.get('/{slug}', response_class=HTMLResponse)
def page(request: Request, slug: str = ''):
    if slug not in PAGES:
        raise HTTPException(status_code=404)
    label, title, description = PAGES[slug]
    return templates.TemplateResponse(request=request, name='page.html', context={
        'slug': slug, 'label': label, 'title': title, 'description': description, 'pages': PAGES,
        'photos': PHOTOS, 'categories': CATEGORIES, 'pairs': PAIRS, 'services': SERVICES,
        'portrait': PORTRAIT, 'hero': HERO, 'not_offered': NOT_OFFERED, 'disclosure': DISCLOSURE,
        'short_disclosure': SHORT_DISCLOSURE, 'registry': REGISTRY,
        'canonical': f'https://ivanpineda.bottah.dev/{slug}',
    })
