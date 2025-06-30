import { defineConfig } from 'vite';
import { readdirSync } from 'fs';
import { resolve } from 'path';

// Build all HTML files in the project root
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
      input: htmlEntries,
    },
  },
  server: {
    historyApiFallback: true,
  },
});
