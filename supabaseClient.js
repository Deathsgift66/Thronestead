import { createClient } from '@supabase/supabase-js';

// Fetch Supabase credentials from the backend at runtime so they are not
// embedded in the built frontend assets.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

function loadConfig() {
  try {
    const req = new XMLHttpRequest();
    req.open('GET', `${API_BASE_URL}/api/public-config/`, false); // synchronous
    req.send(null);
    if (req.status === 200) {
      return JSON.parse(req.responseText);
    }
  } catch {
    // ignore
  }
  return {};
}

const { SUPABASE_URL = '', SUPABASE_ANON_KEY = '' } = loadConfig();

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn('⚠️ Supabase credentials missing.');
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

