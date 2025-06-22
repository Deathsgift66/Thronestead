import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

const SUPABASE_URL = 'https://zzqoxgytfrbptojcwrjm.supabase.co';
const SUPABASE_ANON_KEY =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzIiwicmVmIjoienpxb3hneXRmcmJwdG9qY3dyam0iLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0OTU3OTczNiwiZXhwIjoyMDY1MTU1NzM2fQ.mbFcI9V0ajn51SM68De5ox36VxbPEXK2WK978HZgUaE';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
