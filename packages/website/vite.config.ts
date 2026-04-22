/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// usePolling: file watching across the docker-compose bind-mount needs polling
// (inotify events from the host don't propagate into the container reliably).
//
// hmr.clientPort: In Coder, the dev server is behind a subdomain proxy on 443.
// Locally we leave it unset so the HMR websocket connects on the default port.
const isCoder = !!process.env.CODER_DEPLOYMENT_HOST;

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: { usePolling: true, interval: 200 },
    hmr: isCoder ? { clientPort: 443 } : {},
    allowedHosts: true,
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
