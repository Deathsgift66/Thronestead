import { promises as fs } from 'fs';
import { join, dirname, resolve } from 'path';

const rootDirs = ['Javascript', 'scripts'];
let broken = [];

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fp = join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(fp);
    } else if (entry.isFile() && fp.endsWith('.js')) {
      await checkFile(fp);
    }
  }
}

async function checkFile(file) {
  const data = await fs.readFile(file, 'utf8');
  const importRegex = /import[^\n]*from\s+['"](.+?)['"]/g;
  let match;
  while ((match = importRegex.exec(data))) {
    const spec = match[1];
    if (spec.startsWith('.')) {
      const base = dirname(file);
      const target = resolve(base, spec);
      const candidates = [target, `${target}.js`, join(target, 'index.js')];
      let exists = false;
      for (const c of candidates) {
        try {
          await fs.access(c);
          exists = true;
          break;
        } catch {}
      }
      if (!exists) broken.push(`${file} -> ${spec}`);
    }
  }
}

(async () => {
  for (const dir of rootDirs) {
    await walk(dir);
  }
  if (broken.length) {
    console.error('Broken imports:');
    for (const b of broken) console.error('  ' + b);
    process.exit(1);
  } else {
    console.log('All imports resolved');
  }
})();
