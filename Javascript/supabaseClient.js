/*
Project Name: Kingmakers Rise Frontend
File Name: supabaseClient.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Centralized Supabase Client — supports BOTH .env and fallback — used by all pages

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// ✅ Attempt to pull from .env first
const SUPABASE_URL = import.meta?.env?.VITE_SUPABASE_URL || 'https://zzqoxgytfrbptojcwrjm.supabase.co';
const SUPABASE_ANON_KEY = import.meta?.env?.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6cW94Z3l0ZnJicHRvamN3cmptIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcxMzQ5OTYsImV4cCI6MjA2MjcxMDk5Nn0.Tv_3Na5FFM35FI-p7vIlNj3yAo_WqkKAqLn3fqQ6k3Q';

// ✅ Sanity check — will log warning if using fallback
if (!import.meta?.env?.VITE_SUPABASE_URL || !import.meta?.env?.VITE_SUPABASE_ANON_KEY) {
  console.warn("⚠️ Using fallback Supabase credentials — .env not detected or not loaded.");
}

// ✅ Create the Supabase client
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
