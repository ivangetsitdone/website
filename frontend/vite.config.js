import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
export default defineConfig({
  plugins: [vue()],
  build: { outDir: '../app/static', emptyOutDir: true, lib: { entry: 'main.js', formats: ['es'], fileName: () => 'site.js', cssFileName: 'site' } }
});
