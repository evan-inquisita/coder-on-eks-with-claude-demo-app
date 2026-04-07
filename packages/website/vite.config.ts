/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// usePolling: file watching across the docker-compose bind-mount needs polling
// (inotify events from the host don't propagate into the container reliably).
//
// hmr.clientPort: 443: Coder serves the dev server through its subdomain proxy
// over HTTPS, so the HMR websocket needs to know the browser-visible port.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: { usePolling: true, interval: 200 },
    hmr: { clientPort: 443 },
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
  },
});
