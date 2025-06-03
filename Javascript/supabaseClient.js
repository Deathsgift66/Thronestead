// supabaseClient.js — FINAL UNIVERSAL FALLBACK VERSION — 6.2.25
// Centralized Supabase Client — supports BOTH .env and fallback — used by all pages

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// ✅ Attempt to pull from .env first
const SUPABASE_URL = import.meta?.env?.VITE_SUPABASE_URL || 'https://YOUR_SUPABASE_URL_HERE';
const SUPABASE_ANON_KEY = import.meta?.env?.VITE_SUPABASE_ANON_KEY || 'YOUR_SUPABASE_ANON_KEY_HERE';

// ✅ Sanity check — will log warning if using fallback
if (!import.meta?.env?.VITE_SUPABASE_URL || !import.meta?.env?.VITE_SUPABASE_ANON_KEY) {
  console.warn("⚠️ Using fallback Supabase credentials — .env not detected or not loaded.");
}

// ✅ Create the Supabase client
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
