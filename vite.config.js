import { defineConfig } from 'vite';
import { readdirSync, copyFileSync } from 'fs';
import { resolve } from 'path';

// Discover all HTML files in the project root so Vite builds every page
const htmlEntries = {};
for (const file of readdirSync(__dirname)) {
  if (file.endsWith('.html')) {
    htmlEntries[file.replace('.html', '')] = resolve(__dirname, file);
  }
}

export default defineConfig({
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: htmlEntries,
    },
  },
  server: {
    historyApiFallback: true,
  },
  plugins: [{
    name: 'copy-env',
    buildEnd() {
      try {
        copyFileSync('env.js', resolve(__dirname, 'dist/env.js'));
      } catch {}
    }
  }],
});
