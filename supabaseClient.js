// File: supabaseClient.js
import { createClient } from '@supabase/supabase-js';
import { getEnvVar } from './Javascript/env.js';

const SUPABASE_URL =
  getEnvVar('SUPABASE_URL') || 'https://zzqoxgytfrbptojcwrjm.supabase.co';
const SUPABASE_ANON_KEY =
  getEnvVar('SUPABASE_ANON_KEY') ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6cW94Z3l0ZnJicHRvamN3cmptIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1Nzk3MzYsImV4cCI6MjA2NTE1NTczNn0.mbFcI9V0ajn51SM68De5ox36VxbPEXK2WK978HZgUaE';

// Hard fallback if env is missing — only use these if needed
if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn(
    '⚠️ Missing Supabase credentials. Ensure they are provided via env.js or VITE_ prefix.'
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
