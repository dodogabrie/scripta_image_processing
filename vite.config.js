import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  root: path.resolve(__dirname, 'src/renderer'), // Directory del renderer process
  base: './', // Usa path relativi per gli asset (importante per Electron)
  build: {
    outDir: path.resolve(__dirname, 'dist/renderer'), // Output per il renderer
    emptyOutDir: true,
  },
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src/renderer'),
    },
  },
});