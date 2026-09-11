import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // écoute sur toutes les interfaces réseau (accès depuis le LAN, pas seulement localhost)
    proxy: {
      // En développement, les appels /api/* du frontend sont redirigés vers le backend Express
      // (voir Mission 16 pour l'équivalent en production via Nginx).
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.js',
  },
});
