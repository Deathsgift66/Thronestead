import { createClient } from '@supabase/supabase-js';

// Attempt to load from env.js runtime config first
const runtime = typeof window !== 'undefined' ? window.env || {} : {};

const SUPABASE_URL =
  runtime.VITE_PUBLIC_SUPABASE_URL ||
  import.meta.env.VITE_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY =
  runtime.VITE_PUBLIC_SUPABASE_ANON_KEY ||
  import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn('⚠️ Supabase credentials missing.');
}

export const supabase = createClient(SUPABASE_URL || '', SUPABASE_ANON_KEY || '');

