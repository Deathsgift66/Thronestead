/*
Project Name: Kingmakers Rise Frontend
File Name: supabaseClient.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Centralized Supabase Client — supports BOTH .env and fallback — used by all pages
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from './config.js';

// Initialize Supabase directly from the configuration constants
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
export { supabase };
