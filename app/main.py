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
PAGES = {
    '': ('Home', 'A helping hand for your home.', 'I’m Ivan Pineda, a handyman with 10+ years of hands-on experience. I serve Forest Grove and surrounding communities within a 30-mile radius, during evenings and weekends.'),
    'services': ('Services', 'What can I help you with?', 'From home repairs and shower remodels to fences and yard cleanups, I bring 10+ years of hands-on experience to projects around the home. Serving Forest Grove and surrounding communities within a 30-mile radius.'),
    'about': ('About', 'Hi, I’m Ivan Pineda.', 'I’m the person behind Zip LLC Handyman Services—a hardworking local handyman with 10+ years of experience and a family reason to keep building.'),
    'portfolio': ('Portfolio', 'Work worth sharing.', 'A closer look at my work: showers, flooring, fences, painting and outdoor projects. Explore the details and the stages in between.'),
    'before-after': ('Before & after', 'See the difference.', 'From overgrown spaces to visible progress. A few photo sequences that tell the story behind the work.'),
    'contact': ('Contact me', 'Tell me about your project.', 'Call or text me at 971-288-3488. Serving Forest Grove and surrounding communities within a 30-mile radius, with evening and weekend availability.'),
}
SERVICES = [
    ('Home repairs & interiors', 'General construction experience, sheetrock repairs and flooring. Help with the practical jobs that make a room feel cared for.'),
    ('Showers & bathrooms', 'Shower remodels, tile work and bathroom updates. Browse the project album for a look at work in progress.'),
    ('Painting & surface care', 'Interior and exterior painting, cleaning and pressure washing for spaces that need a fresh start.'),
    ('Fences & outdoor spaces', 'Fencing, patios and retaining walls. Tell me what you have in mind so I can understand the scope.'),
    ('Yards & landscaping', 'Landscaping, yard overhauls and cleanup, from overgrown corners to a more usable outdoor space.'),
    ('Fixtures & small repairs', 'Basic plumbing fixture replacement and repairs, including kitchen and bathroom sinks and toilet swaps or fixes. Experience with basic electrical work such as outlets, switches and lighting.'),
]


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
        'portrait': PORTRAIT,
        'canonical': f'https://ivanpineda.bottah.dev/{slug}',
    })
