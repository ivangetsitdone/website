import json
from pathlib import Path
from datetime import datetime, timezone
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
PAGES = {
    '': ('Home', 'Hello World', 'Zip LLC Handyman Services serves Forest Grove and surrounding communities within a 30-mile radius.'),
    'services': ('Services', 'Built around your project.', 'Serving Forest Grove and surrounding communities within a 30-mile radius. Experience with showers, flooring, fencing, basic plumbing fixture replacement, basic electrical work, and interior and exterior painting. Contact us to discuss your project and confirm the scope of work.'),
    'about': ('About', 'Meet your contractor.', 'Our story, team, and credentials will live here.'),
    'portfolio': ('Portfolio', 'Work worth sharing.', 'A closer look at the work: showers, flooring, fences, painting and outdoor projects. Explore the details and the stages in between.'),
    'before-after': ('Before & after', 'See the difference.', 'From overgrown spaces to visible progress. A few photo sequences that tell the story behind the work.'),
    'contact': ('Contact', 'Let’s build something.', 'Call or text Zip LLC Handyman Services to discuss your project in Forest Grove or the surrounding area within a 30-mile radius. This preview does not collect online submissions.'),
}

@app.get('/healthz')
def health():
    return {'status': 'ok'}

@app.get('/hello', response_class=HTMLResponse)
def hello(request: Request):
    return templates.TemplateResponse(request=request, name='hello.html', context={'time': datetime.now(timezone.utc).strftime('%H:%M:%S UTC')})

@app.get('/', response_class=HTMLResponse)
@app.get('/{slug}', response_class=HTMLResponse)
def page(request: Request, slug: str = ''):
    if slug not in PAGES:
        raise HTTPException(status_code=404)
    label, title, description = PAGES[slug]
    return templates.TemplateResponse(request=request, name='page.html', context={
        'slug': slug, 'label': label, 'title': title, 'description': description, 'pages': PAGES,
        'photos': PHOTOS, 'categories': CATEGORIES, 'pairs': PAIRS,
    })
