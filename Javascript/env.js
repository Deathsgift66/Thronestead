export function getEnvVar(key, defaultValue = '') {
  for (const variant of [key, `PUBLIC_${key}`]) {
    const viteKey = `VITE_${variant}`;

    if (
      typeof import.meta !== 'undefined' &&
      import.meta.env?.[viteKey] !== undefined
    ) {
      return import.meta.env[viteKey];
    }

    if (
      typeof window !== 'undefined' &&
      window.env?.[variant] !== undefined
    ) {
      return window.env[variant];
    }
  }

  return defaultValue;
}
