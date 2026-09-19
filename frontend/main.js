import htmx from 'htmx.org';
import './style.css';
import './gallery.css';
import { mountGalleries } from './gallery';

window.htmx = htmx;

// Boosted navigation swaps the body only, so the head has to be carried across by hand.
// htmx fires afterSwap, then sets <title>, then waits out the settle delay before firing
// htmx:load. Syncing here rather than in mount() means the description and canonical are
// already correct by the time the title changes, instead of ~20ms after it.
function syncHead() {
  const main = document.querySelector('main[data-description]');
  if (!main) return;
  document.querySelector('meta[name="description"]').content = main.dataset.description;
  document.querySelector('link[rel="canonical"]').href = main.dataset.canonical;
}

function mount() {
  mountGalleries();
  syncHead();
}

document.addEventListener('htmx:afterSwap', syncHead);
document.addEventListener('htmx:load', mount);
document.addEventListener('htmx:historyRestore', mount);
mount();
