// Server-rendered links remain usable without JS; enhance them with a native modal.
// The viewer is a scroll-snap carousel: swiping is the browser's own scrolling, and
// the buttons, dots and keyboard shortcuts drive the same scroll position.
const initialized = new WeakSet();
const STAGE_CLASS = stage => `stage stage-${stage.toLowerCase().replace(/ /g, '-')}`;
// Dots stop being useful long before the 35-photo portfolio; that set has the counter.
const MAX_DOTS = 10;

export function mountGalleries() {
  document.querySelectorAll('[data-gallery]').forEach(root => {
    if (initialized.has(root)) return;
    initialized.add(root);
    const cards = [...root.querySelectorAll('[data-photo-card]')];
    const links = cards.map(card => card.querySelector('[data-photo]'));
    const dialog = root.querySelector('dialog');
    const track = dialog.querySelector('[data-track]');
    const dots = dialog.querySelector('[data-dots]');
    const error = dialog.querySelector('[data-image-error]');
    const previous = dialog.querySelector('[data-previous]');
    const next = dialog.querySelector('[data-next]');
    const category = root.querySelector('[data-category-filter]');
    const stage = root.querySelector('[data-stage-filter]');
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    let visible = links;
    let group = [];
    let index = 0;
    let opener;
    // While the carousel is scrolling itself, the observer must not fight it.
    let settling = 0;

    function filter() {
      cards.forEach(card => {
        card.hidden = Boolean((category.value && card.dataset.category !== category.value)
          || (stage.value && card.dataset.stage !== stage.value));
      });
      visible = links.filter(link => !link.closest('[data-photo-card]').hidden);
      root.querySelector('[data-count]').textContent = `${visible.length} of ${links.length} photos`;
      root.querySelector('[data-empty]').hidden = visible.length !== 0;
    }
    if (category) {
      root.querySelector('[data-filters]').hidden = false;
      // HTMX history caches markup, not listeners; reset to a consistent view on restore.
      category.value = '';
      stage.value = '';
      category.addEventListener('change', filter);
      stage.addEventListener('change', filter);
      root.querySelector('[data-reset]').addEventListener('click', () => {
        category.value = '';
        stage.value = '';
        filter();
      });
      filter();
    }

    // Whichever slide fills most of the track is the one being looked at.
    const watcher = new IntersectionObserver(entries => {
      if (settling) return;
      const best = entries.filter(entry => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (best) describe(Number(best.target.dataset.slide));
    }, { root: track, threshold: 0.6 });

    function build(set) {
      watcher.disconnect();
      track.replaceChildren();
      dots.replaceChildren();
      set.forEach((link, position) => {
        const slide = document.createElement('div');
        slide.className = 'viewer-slide';
        slide.dataset.slide = String(position);
        const image = document.createElement('img');
        image.alt = link.dataset.caption;
        image.decoding = 'async';
        image.dataset.source = link.href;
        image.addEventListener('error', () => {
          slide.dataset.failed = 'true';
          if (position === index) error.hidden = false;
        });
        // The stage tag rides with the photograph, so it stays readable mid-swipe.
        const tag = document.createElement('span');
        tag.className = STAGE_CLASS(link.dataset.stage);
        tag.textContent = link.dataset.stage;
        slide.append(image, tag);
        track.append(slide);
        watcher.observe(slide);
        if (set.length > 1 && set.length <= MAX_DOTS) {
          const dot = document.createElement('button');
          dot.type = 'button';
          dot.setAttribute('aria-label', `Photo ${position + 1}: ${link.dataset.title}`);
          dot.addEventListener('click', () => go(position));
          dots.append(dot);
        }
      });
      dots.hidden = dots.children.length === 0;
      previous.disabled = set.length < 2;
      next.disabled = set.length < 2;
    }

    // Only the neighbours are fetched: a 35-photo set must not pull 35 full images.
    function load(position) {
      for (const near of [position, position - 1, position + 1]) {
        const image = track.children[near]?.firstElementChild;
        if (image && !image.src) image.src = image.dataset.source;
      }
    }

    function describe(position) {
      index = position;
      const link = group[index];
      load(index);
      error.hidden = track.children[index].dataset.failed !== 'true';
      dialog.querySelector('#viewer-title').textContent = link.dataset.title;
      dialog.querySelector('#viewer-caption').textContent = link.dataset.caption;
      dialog.querySelector('[data-viewer-category]').textContent =
        `${link.closest('[data-photo-card]').dataset.category} · ${link.dataset.stage}`;
      dialog.querySelector('[data-viewer-count]').textContent = `${index + 1} / ${group.length}`;
      [...dots.children].forEach((dot, position) => {
        dot.setAttribute('aria-current', String(position === index));
      });
    }

    function scrollTo(position, smooth) {
      settling += 1;
      track.scrollTo({ left: position * track.clientWidth, behavior: smooth ? 'smooth' : 'auto' });
      setTimeout(() => { settling = Math.max(0, settling - 1); }, smooth ? 450 : 60);
    }

    function go(next_) {
      const position = (next_ + group.length) % group.length;
      const stride = Math.abs(position - index) === 1;
      describe(position);
      scrollTo(position, stride && !motion.matches);
    }

    root.addEventListener('click', event => {
      const link = event.target.closest('[data-photo]');
      if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      opener = link;
      // Inside a project the carousel is that project; elsewhere it is the whole set.
      const sequence = link.closest('.sequence-grid');
      group = sequence ? [...sequence.querySelectorAll('[data-photo]')] : visible;
      build(group);
      dialog.showModal();
      describe(Math.max(0, group.indexOf(link)));
      scrollTo(index, false);
    });
    dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
    previous.addEventListener('click', () => go(index - 1));
    next.addEventListener('click', () => go(index + 1));
    dialog.addEventListener('keydown', event => {
      if (event.key === 'Tab') {
        const controls = [...dialog.querySelectorAll('button:not(:disabled)')];
        const first = controls[0];
        const last = controls.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        go(index + (event.key === 'ArrowRight' ? 1 : -1));
      }
      if (event.key === 'Home' || event.key === 'End') {
        event.preventDefault();
        go(event.key === 'Home' ? 0 : group.length - 1);
      }
    });
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    });
    dialog.addEventListener('close', () => {
      watcher.disconnect();
      track.replaceChildren();
      if (opener?.isConnected) opener.focus({ preventScroll: true });
    });
    // Don't restore an open, non-modal <dialog> from a serialized history snapshot.
    dialog.removeAttribute('open');
  });
}

document.addEventListener('htmx:beforeHistorySave', () => {
  document.querySelectorAll('[data-gallery] dialog[open]').forEach(dialog => dialog.close());
});
