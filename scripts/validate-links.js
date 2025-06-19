import { promises as fs, existsSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { load } from 'cheerio';

const distDir = resolve('dist');
let broken = 0;

async function getHtmlFiles(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const res = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await getHtmlFiles(res));
    } else if (entry.isFile() && res.endsWith('.html')) {
      files.push(res);
    }
  }
  return files;
}

function isInternal(href) {
  return href && !href.startsWith('http://') && !href.startsWith('https://') &&
    !href.startsWith('#') && !href.startsWith('mailto:') && !href.startsWith('javascript:');
}

function checkExists(base, href) {
  const withoutHash = href.split('#')[0];
  const path = withoutHash.startsWith('/') ?
    join(distDir, withoutHash.replace(/^\//, '')) :
    join(base, withoutHash);

  if (existsSync(path)) return true;

  if (!path.endsWith('.html')) {
    if (existsSync(path + '.html')) return true;
    if (existsSync(join(path, 'index.html'))) return true;
  }
  return false;
}

async function validate() {
  const htmlFiles = await getHtmlFiles(distDir);
  for (const file of htmlFiles) {
    const html = await fs.readFile(file, 'utf8');
    const $ = load(html);
    const dir = dirname(file);
    $('a[href]').each((_, el) => {
      const href = $(el).attr('href');
      if (isInternal(href) && !checkExists(dir, href)) {
        console.warn(`Missing link target: '${href}' referenced in ${file}`);
        broken += 1;
      }
    });
  }
  if (broken) {
    console.error(`Found ${broken} broken link${broken !== 1 ? 's' : ''}.`);
    process.exit(1);
  }
}

validate().catch(err => {
  console.error(err);
  process.exit(1);
});
