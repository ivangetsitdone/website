import htmx from 'htmx.org';
import './style.css';
import './gallery.css';
import { mountGalleries } from './gallery';

window.htmx = htmx;
function mount() {
  mountGalleries();
  // Boosted navigation swaps the body; keep head metadata in sync with each page.
  const main = document.querySelector('main[data-description]');
  if (main) {
    document.querySelector('meta[name="description"]').content = main.dataset.description;
    document.querySelector('link[rel="canonical"]').href = main.dataset.canonical;
  }
}
document.addEventListener('htmx:load', mount);
document.addEventListener('htmx:historyRestore', mount);
mount();
