"""One-time import of the owner's September 2026 upload; retained for provenance.

Run from project root: python3 scripts/curate_photos.py
Original source images are versioned; generated web images are not.
"""
import hashlib
import json
import shutil
from pathlib import Path

# Numbers refer to the sorted original filenames, not project chronology.
ENTRIES = [
    (12, 'Wood & wire garden fence', 'Fencing', 'Detail', 'Warm-toned wood rails frame wire panels beside a green lawn and gravel border.'),
    (29, 'Mosaic niches taking shape', 'Showers & tile', 'In progress', 'Marble-look wall tiles surround two stacked mosaic niches. The tub edge and tools show this is still a work site.'),
    (7, 'Wood-look flooring through the room', 'Interiors', 'Detail', 'Warm wood-look planks run through the room toward a bright doorway, with white trim at the edges.'),
    (42, 'Garden steps revealed', 'Outdoor projects', 'After', 'A defined flight of garden steps leads toward the gate, with the surrounding soil still exposed.'),
    (11, 'Exterior with a blue entry', 'Painting', 'Detail', 'Light-colored siding and trim frame a vivid blue front door beneath the tall roofline.'),
    (22, 'Side yard after clearing', 'Outdoor projects', 'After', 'The side passage is open again, revealing three raised planting beds along the chain-link fence.'),
    (25, 'Privacy fence from the inside', 'Fencing', 'Detail', 'Vertical wood boards are supported by horizontal rails and dark posts along a narrow planted boundary.'),
    (38, 'Shower wall preparation', 'Showers & tile', 'In progress', 'Red-coated wall boards and two recessed niches are visible before the tile goes on; the tub below is protected.'),
    (36, 'Tile installation underway', 'Showers & tile', 'In progress', 'Marble-look tiles and a mosaic niche are being fitted, with tile spacers and red-coated wall areas still visible.'),
    (32, 'Tub surround and mosaic band', 'Showers & tile', 'In progress', 'A horizontal mosaic accent runs into the stacked niches above the tub. Masking tape remains along the ceiling edge.'),
    (15, 'Recessed shower shelf', 'Showers & tile', 'Detail', 'A mosaic-backed shelf is inset into a light tile shower wall, keeping bottles within reach.'),
    (16, 'Shower enclosure overview', 'Showers & tile', 'Detail', 'A light-colored shower enclosure with a curtain rail, wall-mounted grab bar and recessed shelf.'),
    (6, 'Flooring at the doorway', 'Interiors', 'Detail', 'Wood-look flooring meets white baseboards and a doorway, with blue masking tape still visible on the trim.'),
    (30, 'Cool gray room palette', 'Interiors', 'In progress', 'Gray walls, white baseboards and gray-brown plank flooring meet beneath a small window; supplies remain on the floor.'),
    (31, 'Room viewed from the hall', 'Interiors', 'In progress', 'A doorway view shows the gray room, contrasting white trim and plank floor while cleanup is still underway.'),
    (47, 'Open wall and insulation', 'Interiors', 'In progress', 'Exposed wall studs and insulation show an interior room during the wall-preparation stage.'),
    (45, 'Drywall seams in progress', 'Interiors', 'In progress', 'Drywall panels have taped and coated seams, while tools and materials remain on the unfinished floor.'),
    (8, 'A bold blue front door', 'Painting', 'In progress', 'A paneled entry door has a bright blue finish, with masking tape and painting supplies still around the threshold.'),
    (9, 'Exterior siding during the work', 'Painting', 'In progress', 'A horizontal gray-blue strip contrasts with light siding while the adjacent corner trim remains exposed.'),
    (10, 'Light siding and trim', 'Painting', 'In progress', 'Light-colored horizontal siding fills the wall, with a paint can and supplies at ground level.'),
    (13, 'Fence following the lawn', 'Fencing', 'Detail', 'Wood-and-wire fence panels follow the edge of a sloping lawn, with a gravel strip along the base.'),
    (14, 'Added privacy above the fence', 'Fencing', 'Detail', 'A row of taller warm-toned boards rises above an older weathered fence section.'),
    (26, 'Fence framework underway', 'Fencing', 'In progress', 'Dark posts and horizontal wood rails mark out a fence line beside the street before the infill is installed.'),
    (4, 'Wood privacy fence line', 'Fencing', 'Detail', 'Close-set vertical wood boards form a continuous privacy fence along a narrow side passage.'),
    (2, 'Fence-post hardware detail', 'Fencing', 'Detail', 'A dark metal fence-post component sits beside an existing wood rail, showing the connection area up close.'),
    (18, 'Side yard before clearing', 'Outdoor projects', 'Before', 'Tall grass and dense weeds fill the narrow passage between the house and the chain-link fence.'),
    (21, 'Cleared garden area', 'Outdoor projects', 'Detail', 'An open garden area surrounds raised beds beneath a mature tree, with scattered clippings still on the ground.'),
    (41, 'Garden steps during excavation', 'Outdoor projects', 'In progress', 'Grass and soil cover parts of the existing steps, while a dug-out lower section and shovel show work underway.'),
    (40, 'Paved garden landing', 'Outdoor projects', 'Detail', 'Rectangular pavers form a small landing and path beside a planted border.'),
    (43, 'Leaf-covered sidewalk edge', 'Outdoor projects', 'Before', 'Fallen leaves blanket the strip between a wooded slope and the sidewalk. A matching final view is not confirmed.'),
    (44, 'Cleared sidewalk border', 'Outdoor projects', 'Detail', 'The ground beside a wooded sidewalk has been cleared back, exposing soil around the tree trunks.'),
    (23, 'Parking area work underway', 'Outdoor projects', 'In progress', 'A broad asphalt parking area with cones and people in the distance during site work.'),
    (24, 'Parking bay markings', 'Outdoor projects', 'Detail', 'Bright white parking-space lines cross the asphalt, with cones still standing in the lot.'),
    (1, 'Asphalt patch detail', 'Outdoor projects', 'Detail', 'A rectangular dark asphalt patch contrasts with the older pavement around it.'),
    (54, 'Landscape block course', 'Outdoor projects', 'In progress', 'Textured landscape blocks form a low course against exposed soil, with the hollow block tops still visible.'),
]

PAIRS = [
    {'id': 'side-yard', 'title': 'Opening up a side yard', 'photos': ['p18', 'p22'],
     'note': 'Likely before / after: the deck, satellite dish, neighboring wall and fence align in both views.'},
    {'id': 'garden-steps', 'title': 'Finding the steps again', 'photos': ['p41', 'p42'],
     'note': 'Likely progress / after: the gate, silver-leaved planting and stair position match. The first photo already shows excavation underway.'},
    {'id': 'shower-tile', 'title': 'From wall preparation to tile', 'photos': ['p38', 'p36', 'p29'],
     'note': 'Likely work sequence: two stacked niches and the same tub corner connect these views. These are progress photos, not a completed shower.'},
]

if __name__ == '__main__':
    files = sorted(Path('recovery/uploads').glob('*.jpeg'))
    assert len(files) == 54, 'Expected the original 54-photo upload; do not silently remap IDs.'
    target = Path('content/photos')
    target.mkdir(parents=True, exist_ok=True)
    photos = []
    for number, title, category, stage, caption in ENTRIES:
        source = files[number - 1]
        photo_id = f'p{number:02d}'
        shutil.copyfile(source, target / f'{photo_id}.jpg')
        photos.append(dict(id=photo_id, title=title, category=category, stage=stage,
                           caption=caption, source=source.name,
                           sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    Path('app/data').mkdir(exist_ok=True)
    Path('app/data/portfolio.json').write_text(json.dumps({'photos': photos, 'pairs': PAIRS}, indent=2) + '\n')
    print(f'Imported {len(photos)} source photos; {len(PAIRS)} provisional sequences.')
