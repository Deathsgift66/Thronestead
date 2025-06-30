import { createClient } from '@supabase/supabase-js';

// Supabase credentials are supplied via environment variables at build time.
// When absent the values may be provided on `window.env` or fetched from the
// backend's `/api/public-config` endpoint at runtime.

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || window.env?.API_BASE_URL || '';

let SUPABASE_URL =
  import.meta.env.VITE_PUBLIC_SUPABASE_URL || window.env?.SUPABASE_URL;
let SUPABASE_ANON_KEY =
  import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY || window.env?.SUPABASE_ANON_KEY;

if ((!SUPABASE_URL || !SUPABASE_ANON_KEY) && API_BASE_URL) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/public-config`);
    if (res.ok) {
      const cfg = await res.json();
      SUPABASE_URL ||= cfg.SUPABASE_URL;
      SUPABASE_ANON_KEY ||= cfg.SUPABASE_ANON_KEY;
      window.env = window.env || {};
      if (cfg.SUPABASE_URL) window.env.SUPABASE_URL = cfg.SUPABASE_URL;
      if (cfg.SUPABASE_ANON_KEY) window.env.SUPABASE_ANON_KEY = cfg.SUPABASE_ANON_KEY;
    }
  } catch (err) {
    console.warn('Failed to load Supabase config at runtime:', err);
  }
}

export const supabaseReady = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

if (!supabaseReady) {
  console.warn(
    'Supabase credentials missing. Ensure VITE_PUBLIC_SUPABASE_URL and VITE_PUBLIC_SUPABASE_ANON_KEY are set or available via runtime config.'
  );
}

export const supabase = supabaseReady
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: { persistSession: false }
    })
  : null;


