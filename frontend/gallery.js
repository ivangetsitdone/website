// Server-rendered links remain usable without JS; enhance them with a native modal.
const initialized = new WeakSet();

export function mountGalleries() {
  document.querySelectorAll('[data-gallery]').forEach(root => {
    if (initialized.has(root)) return;
    initialized.add(root);
    const cards = [...root.querySelectorAll('[data-photo-card]')];
    const links = cards.map(card => card.querySelector('[data-photo]'));
    const dialog = root.querySelector('dialog');
    const image = dialog.querySelector('[data-viewer-image]');
    const error = dialog.querySelector('[data-image-error]');
    const category = root.querySelector('[data-category-filter]');
    const stage = root.querySelector('[data-stage-filter]');
    let visible = links;
    let index = 0;
    let opener;

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

    function show(nextIndex) {
      index = (nextIndex + visible.length) % visible.length;
      const link = visible[index];
      error.hidden = true;
      image.alt = link.dataset.caption;
      image.src = link.href;
      dialog.querySelector('#viewer-title').textContent = link.dataset.title;
      dialog.querySelector('#viewer-caption').textContent = link.dataset.caption;
      dialog.querySelector('[data-viewer-stage]').textContent = link.dataset.stage;
      dialog.querySelector('[data-viewer-count]').textContent = `${index + 1} / ${visible.length}`;
      dialog.querySelector('[data-previous]').disabled = visible.length < 2;
      dialog.querySelector('[data-next]').disabled = visible.length < 2;
    }
    image.addEventListener('error', () => { error.hidden = false; });
    root.addEventListener('click', event => {
      const link = event.target.closest('[data-photo]');
      if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      opener = link;
      show(visible.indexOf(link));
      dialog.showModal();
    });
    dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
    dialog.querySelector('[data-previous]').addEventListener('click', () => show(index - 1));
    dialog.querySelector('[data-next]').addEventListener('click', () => show(index + 1));
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
        show(index + (event.key === 'ArrowRight' ? 1 : -1));
      }
    });
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    });
    dialog.addEventListener('close', () => {
      image.removeAttribute('src');
      if (opener?.isConnected) opener.focus({ preventScroll: true });
    });
    // Don't restore an open, non-modal <dialog> from a serialized history snapshot.
    dialog.removeAttribute('open');
  });
}

document.addEventListener('htmx:beforeHistorySave', () => {
  document.querySelectorAll('[data-gallery] dialog[open]').forEach(dialog => dialog.close());
});
