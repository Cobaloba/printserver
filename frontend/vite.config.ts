import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    tailwindcss(),
    sveltekit(),
    VitePWA({ registerType: 'autoUpdate' })
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:9000'
    }
  }
});
