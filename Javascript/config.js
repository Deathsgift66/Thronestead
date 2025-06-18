// Project Name: Thronestead©
// File Name: config.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
/*
  config.js — Public Supabase configuration (non-secret) used by frontend
  Automatically fallback to environment overrides if present (e.g., Render env vars)
*/

const ENV = (typeof import !== 'undefined' && import.meta && import.meta.env) ? import.meta.env : (window.ENV || {});

export const SUPABASE_URL = ENV.VITE_SUPABASE_URL || window.SUPABASE_URL || '';

// ❗ Public anon key — NEVER use service_role key in frontend.
export const SUPABASE_ANON_KEY = ENV.VITE_SUPABASE_ANON_KEY || window.SUPABASE_ANON_KEY || '';

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error(
    'Supabase credentials missing. Define VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in env.js',
  );
}

// Optional: Override API base URL (for FastAPI or Express proxy)
export const API_BASE_URL =
  ENV.VITE_API_BASE_URL ||
  window.API_BASE_URL ||
  (location.port === '3000' ? 'http://localhost:8000' : '');
