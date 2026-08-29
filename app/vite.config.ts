import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    // The API is same-origin in the browser, so nothing needs CORS and no base URL is
    // configured per environment — one fewer thing to get wrong between dev and deploy.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  test: { globals: true, environment: 'node' },
});
