import htmx from 'htmx.org';
import { createApp } from 'vue';
import Hello from './Hello.vue';
import './style.css';
window.htmx = htmx;
const mounted = new Map();
function mount() {
  document.querySelectorAll('[data-vue-hello]').forEach(el => {
    if (!mounted.has(el)) { const app = createApp(Hello); app.mount(el); mounted.set(el, app); }
  });
}
document.addEventListener('htmx:beforeCleanupElement', event => {
  for (const [el, app] of mounted) {
    if (event.detail.elt === el || event.detail.elt.contains(el)) { app.unmount(); mounted.delete(el); }
  }
});
document.addEventListener('htmx:load', mount);
document.addEventListener('htmx:historyRestore', mount);
mount();
