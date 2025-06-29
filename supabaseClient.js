import { createClient } from '@supabase/supabase-js';

// Supabase credentials are supplied via Vite environment variables.
// The variables are injected at build time. See `.env.example` for details.
const SUPABASE_URL = import.meta.env.VITE_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_PUBLIC_SUPABASE_ANON_KEY;

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

