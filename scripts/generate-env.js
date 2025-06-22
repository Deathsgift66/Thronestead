import { writeFileSync, readFileSync, existsSync } from 'fs';

function loadEnv(path) {
  if (!existsSync(path)) return {};
  const out = {};
  for (const line of readFileSync(path, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^([^#=]+)=([\s\S]*)$/);
    if (match) out[match[1].trim()] = match[2].trim();
  }
  return out;
}

const local = loadEnv('.env');

const SUPABASE_URL = process.env.SUPABASE_URL || local.SUPABASE_URL || '';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || local.SUPABASE_ANON_KEY || '';
const API_BASE_URL = process.env.API_BASE_URL || local.API_BASE_URL || '';

const content = `export const SUPABASE_URL = '${SUPABASE_URL}';
export const SUPABASE_ANON_KEY = '${SUPABASE_ANON_KEY}';
export const API_BASE_URL = '${API_BASE_URL}';

window.ENV = {
  SUPABASE_URL,
  SUPABASE_ANON_KEY,
  API_BASE_URL,
};

window.API_BASE_URL = API_BASE_URL;
`;

writeFileSync('env.js', content);
console.log('env.js generated');
