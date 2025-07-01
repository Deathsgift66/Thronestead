export function getEnvVar(key, defaultValue = '') {
  const variants = [key, `PUBLIC_${key}`];
  const prefixes = ['', 'BACKUP_', 'FALLBACK_', 'DEFAULT_'];

  for (const prefix of prefixes) {
    for (const variant of variants) {
      const viteKey = `VITE_${prefix}${variant}`;
      try {
        if (typeof import.meta !== 'undefined' &&
            import.meta.env &&
            typeof import.meta.env[viteKey] !== 'undefined') {
          return import.meta.env[viteKey];
        }
      } catch (err) {
        // ignore access errors on import.meta in unsupported environments
      }

      try {
        if (typeof window !== 'undefined' &&
            window.env &&
            typeof window.env[`${prefix}${key}`] !== 'undefined') {
          return window.env[`${prefix}${key}`];
        }
      } catch (err) {
        // ignore access errors on window.env
      }
    }
  }

  return defaultValue;
}
