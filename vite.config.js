import { defineConfig } from 'vite';
import { readdirSync } from 'fs';
import { resolve } from 'path';

// Dynamically collect all .html files from project root
const htmlEntries = {};
for (const file of readdirSync(__dirname)) {
  if (file.endsWith('.html')) {
    htmlEntries[file.replace('.html', '')] = resolve(__dirname, file);
  }
}

export default defineConfig({
  build: {
    target: 'es2022',
    outDir: 'dist',
    rollupOptions: {
      input: htmlEntries, // Multiple HTML entry points
    },
  },
  server: {
    // Optional: expose port and enable CORS during local dev
    port: 5173,
    cors: true,
  },
});
