export function getEnvVar(key, defaultValue = '') {
  const variants = [key, `PUBLIC_${key}`];

  for (const variant of variants) {
    const viteKey = `VITE_${variant}`;
    try {
      if (typeof import.meta !== 'undefined' &&
          import.meta.env &&
          typeof import.meta.env[viteKey] !== 'undefined') {
        return import.meta.env[viteKey];
      }
    } catch {
      // ignore
    }

    try {
      if (typeof window !== 'undefined' &&
          window.env &&
          typeof window.env[variant] !== 'undefined') {
        return window.env[variant];
      }
    } catch {
      // ignore
    }
  }

  return defaultValue;
}
