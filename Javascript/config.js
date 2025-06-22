// Project Name: Thronestead©
// File Name: config.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
/*
  config.js — Public Supabase configuration (non-secret) used by frontend
  Automatically fallback to environment overrides if present (e.g., Render env vars)
*/

let ENV = typeof window !== 'undefined' && window.ENV
  ? window.ENV
  : {};

let SUPABASE_URL = ENV.SUPABASE_URL || '';
let SUPABASE_ANON_KEY = ENV.SUPABASE_ANON_KEY || '';

// Attempt to dynamically load env.js if values are missing
if ((!SUPABASE_URL || !SUPABASE_ANON_KEY) && typeof window !== 'undefined') {
  (async () => {
    try {
      const mod = await import('../env.js');
      ENV = { ...mod, ...ENV };
      window.ENV ||= ENV;
      SUPABASE_URL ||= mod.SUPABASE_URL;
      SUPABASE_ANON_KEY ||= mod.SUPABASE_ANON_KEY;
    } catch {
      // env.js optional; credentials may come from API
    }
  })();
}

export { SUPABASE_URL, SUPABASE_ANON_KEY };

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error(
    'Supabase credentials missing. Define SUPABASE_URL/SUPABASE_ANON_KEY in env.js',
  );
}

// Optional: Override API base URL (for FastAPI or Express proxy)
export const API_BASE_URL =
  ENV.API_BASE_URL || 'https://thronestead.onrender.com';
