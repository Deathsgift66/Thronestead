// Project Name: Kingmakers Rise©
// File Name: supabaseClient.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// ✅ Centralized Supabase Client
// This file initializes and exports the Supabase client used across all frontend modules.

// Uses Supabase’s ESM-compatible CDN version (suitable for native ES module support in modern browsers)
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// ✅ Environment-safe import
// These constants should be defined in `config.js` and vary per deployment environment (dev, staging, production)
import { SUPABASE_URL, SUPABASE_ANON_KEY } from './config.js';

// ✅ Create the Supabase client instance
// This allows you to make authenticated requests, real-time subscriptions, and database queries
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ✅ Export client globally
// Every script that needs to interact with Supabase will import it from this single source
export { supabase };
