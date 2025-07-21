const metaEnv = typeof import.meta !== 'undefined' ? import.meta.env || {} : {};
const runtimeEnv =
  typeof window !== 'undefined' && window.env ? window.env : {};

const DEFAULTS = {
  API_BASE_URL: 'https://your-production-api-url.com',
};

const PREFIXES = ['', 'VITE_', 'PUBLIC_', 'BACKUP_', 'FALLBACK_', 'DEFAULT_'];

const cache = {};

export function getEnvVar(name) {
  if (name in cache) return cache[name];

  for (const src of [metaEnv, runtimeEnv]) {
    for (const pre of PREFIXES) {
      const key = pre + name;
      if (src && src[key]) {
        cache[name] = src[key];
        return cache[name];
      }
    }
  }

  cache[name] = DEFAULTS[name];
  return cache[name];
}
