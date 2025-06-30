import { createClient } from '@supabase/supabase-js';

// Supabase credentials are supplied via Vite environment variables.
// The variables are injected at build time. See `.env.example` for details.
const SUPABASE_URL =
  import.meta.env.VITE_PUBLIC_SUPABASE_URL || window.env?.SUPABASE_URL;
const SUPABASE_ANON_KEY =
  import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY || window.env?.SUPABASE_ANON_KEY;

export const supabaseReady = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

if (!supabaseReady) {
  console.warn(
    'Supabase credentials missing. Ensure VITE_PUBLIC_SUPABASE_URL and VITE_PUBLIC_SUPABASE_ANON_KEY are set.'
  );
}

if (supabaseReady && !window.__supabaseClient) {
  window.__supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: { persistSession: false }
  });
}

export const supabase = supabaseReady ? window.__supabaseClient : null;


