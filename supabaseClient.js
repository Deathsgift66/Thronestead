import { createClient } from '@supabase/supabase-js';

// Hard-coded Supabase credentials supplied by the user.
// NOTE: Do not expose sensitive keys in production builds.
const SUPABASE_URL = 'https://zzqoxgytfrbptojcwrjm.supabase.co';
const SUPABASE_ANON_KEY =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6cW94Z3l0ZnJicHRvamN3cmptIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1Nzk3MzYsImV4cCI6MjA2NTE1NTczNn0.mbFcI9V0ajn51SM68De5ox36VxbPEXK2WK978HZgUaE';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

