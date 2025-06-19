import { resolve } from 'path';
import { readdirSync } from 'fs';

const htmlEntries = {};
for (const file of readdirSync(__dirname)) {
  if (file.endsWith('.html')) {
    const name = file.replace(/\.html$/, '');
    htmlEntries[name] = resolve(__dirname, file);
  }
}

export default {
  base: '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      input: htmlEntries
    }
  }
};
