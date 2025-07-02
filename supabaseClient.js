// File: supabaseClient.js
import { createClient } from '@supabase/supabase-js';
import { getEnvVar } from './Javascript/env.js';

const SUPABASE_URL = getEnvVar('SUPABASE_URL');
const SUPABASE_ANON_KEY = getEnvVar('SUPABASE_ANON_KEY');

// Warn when credentials are missing rather than using a bundled fallback
if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn(
    '⚠️ Missing Supabase credentials. Provide them via env.js or VITE_* variables.'
  );
}

// Avoid creating multiple instances
if (!window.__supabaseClient && SUPABASE_URL && SUPABASE_ANON_KEY) {
  window.__supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      persistSession: true,
      // Disable built-in auto refresh to avoid duplicate refresh calls
      // which can invalidate the token when our custom logic runs.
      autoRefreshToken: false,
    },
  });
}

export const supabase = window.__supabaseClient || null;
export const supabaseReady = Boolean(supabase);
