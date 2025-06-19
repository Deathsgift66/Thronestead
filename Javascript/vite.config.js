import { defineConfig } from 'vite';
import { resolve } from 'path';
import fs from 'fs';

const htmlFiles = fs
  .readdirSync(__dirname)
  .filter((f) => f.endsWith('.html'));

const input = Object.fromEntries(
  htmlFiles.map((f) => [f.replace(/\.html$/, ''), resolve(__dirname, f)])
);

export default defineConfig({
  build: {
    rollupOptions: {
      input
    }
  }
});
