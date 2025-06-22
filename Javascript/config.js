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

// Attempt to dynamically load env.js if values are missing
if ((!ENV.SUPABASE_URL || !ENV.SUPABASE_ANON_KEY) && typeof window !== 'undefined') {
  try {
    const mod = await import('../env.js');
    ENV = { ...mod, ...ENV };
    window.ENV ||= ENV;
  } catch {
    // env.js optional; credentials may come from API
  }
}

export const SUPABASE_URL =
  ENV.SUPABASE_URL || '';

// ❗ Public anon key — NEVER use service_role key in frontend.
export const SUPABASE_ANON_KEY =
  ENV.SUPABASE_ANON_KEY || '';

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error(
    'Supabase credentials missing. Define SUPABASE_URL/SUPABASE_ANON_KEY in env.js',
  );
}

// Optional: Override API base URL (for FastAPI or Express proxy)
export const API_BASE_URL =
  ENV.API_BASE_URL || 'https://thronestead.onrender.com';
