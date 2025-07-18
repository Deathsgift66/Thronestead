// Project: Thronestead©
// File: authGuard.js
// Version: 1.0.2025.07.18
// Author: Deathsgift66 (Final Production-Hardened)

// Description:
// Universal gatekeeper for all protected frontend pages.
// Ensures only verified Supabase users with completed setup can access pages.
// Blocks unauthorized access, prevents race conditions, enforces admin guards.

import { supabase } from '../../supabaseClient.js';
import { getEnvVar } from '../env.js';
import { startSessionRefresh } from '../auth.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';

// Hardened flags and constants
const PUBLIC_PATHS = new Set([
  '/index.html',
  '/about.html',
  '/projects.html',
  '/login.html',
  '/signup.html',
  '/update-password.html',
  '/legal.html',
  '/404.html'
]);

const pathname = window.location.pathname;

// Admin flag now based on secure meta tag, not window-level spoofing
const requireAdmin = document.querySelector('meta[name="require-admin"]')?.content === 'true';

(async function authGuard() {
  if (PUBLIC_PATHS.has(pathname)) return;

  if (requireAdmin) document.documentElement.style.display = 'none';

  try {
    // Step 1: Get valid session
    let { data: { session } } = await supabase.auth.getSession();

    if (!session?.access_token) {
      const { data: refreshed } = await supabase.auth.refreshSession();
      session = refreshed?.session;
    }

    if (!session?.access_token) return redirect('/login.html');

    // Step 2: Validate session with backend
    const API_BASE_URL = getEnvVar('API_BASE_URL');
    const authCheck = await fetch(`${API_BASE_URL}/api/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });

    if (!authCheck.ok) return redirect('/login.html');

    // Step 3: Get user from session or fallback
    let user = session.user;
    if (!user) {
      const { data: { user: refreshedUser }, error } = await supabase.auth.getUser();
      user = refreshedUser;
    }

    if (!user) return redirect('/login.html');

    // Step 4: Fetch internal user profile
    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();

    if (!userData || userErr) return redirect('/login.html');
    if (!userData.setup_complete) return redirect('/play.html');
    if (requireAdmin && userData.is_admin !== true) return redirect('/overview.html');

    // Step 5: Start token refresh cycle
    startSessionRefresh();

    // Step 6: Store user globally
    window.user = { id: user.id, is_admin: userData.is_admin };

    if (requireAdmin) document.documentElement.style.display = '';

    // Step 7: Load progression safely
    try {
      loadPlayerProgressionFromStorage();
      if (!window.playerProgression) {
        await fetchAndStorePlayerProgression(user.id);
      }
    } catch (e) {
      console.warn('[AuthGuard] Player progression failed to load:', e);
    }

  } catch (err) {
    console.error('[AuthGuard] Fatal error:', err);
    document.documentElement.style.display = '';
    redirect('/login.html');
  }
})();

// Secure redirect function: hard stop with unload protection
function redirect(path) {
  window.location.replace(path);
  throw new Error(`Redirecting to ${path}`);
}
