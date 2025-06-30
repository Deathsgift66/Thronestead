export function getEnvVar(key, defaultValue = '') {
  const variants = [key, `PUBLIC_${key}`];
  const prefixes = ['', 'BACKUP_', 'FALLBACK_', 'DEFAULT_'];
  for (const prefix of prefixes) {
    for (const variant of variants) {
      const viteKey = `VITE_${prefix}${variant}`;
      const viteVal = import.meta.env[viteKey];
      if (viteVal) return viteVal;
    }
    const winVal = window.env?.[`${prefix}${key}`];
    if (winVal) return winVal;
  }
  return defaultValue;
}
