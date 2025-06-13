/*
Project Name: Kingmakers Rise Frontend
File Name: supabaseClient.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Centralized Supabase Client — supports BOTH .env and fallback — used by all pages
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
import { loadConfig } from './config.js';

const { SUPABASE_URL, SUPABASE_ANON_KEY } = await loadConfig();
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
