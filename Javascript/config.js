// config.js — loads public configuration from the backend
let configPromise;

export function loadConfig() {
  if (!configPromise) {
    configPromise = fetch('/api/public-config')
      .then(r => {
        if (!r.ok) throw new Error('Failed to load public config');
        return r.json();
      });
  }
  return configPromise;
}
