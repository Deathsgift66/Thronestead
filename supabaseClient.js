import { createClient } from '@supabase/supabase-js';

// Attempt to load from env.js runtime config first
const runtime = typeof window !== 'undefined' ? window.env || {} : {};

const supabaseUrl = runtime.SUPABASE_URL || import.meta.env.SUPABASE_URL || import.meta.env.VITE_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = runtime.SUPABASE_ANON_KEY || import.meta.env.SUPABASE_ANON_KEY || import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('⚠️ SUPABASE_URL or SUPABASE_ANON_KEY is undefined. Check your environment configuration.');
}

export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '');

