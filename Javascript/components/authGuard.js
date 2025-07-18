// Project: Thronestead©
// File: authGuard.js
// Version: 1.1.2025.07.18
// Author: Deathsgift66 (Final Production-Hardened)

// Description:
// Gatekeeper for all secure pages. Ensures only verified Supabase users
// with a complete profile can access protected pages. Prevents race conditions,
// enforces admin-only views, validates session against backend, and syncs player progression.

import { supabase } from '../../supabaseClient.js';
import { getEnvVar } from '../env.js';
import { startSessionRefresh } from '../auth.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';

// Constants
const PUBLIC_PATHS = new Set([
  '/index.html',
  '/about.html',
  '/profile.html',
  '/login.html',
  '/signup.html',
  '/update-password.html',
  '/legal.html',
  '/404.html',
]);

const pathname = window.location.pathname.split('?')[0].split('#')[0];
const requireAdmin = document.querySelector('meta[name="require-admin"]')?.content === 'true';

// Entry
(async function authGuard() {
  if (PUBLIC_PATHS.has(pathname)) return;

  // Lock screen while auth check runs
  if (requireAdmin) document.documentElement.style.display = 'none';

  try {
    let { data: { session } } = await supabase.auth.getSession();

    // Check token expiration
    const isExpired = (token) => {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return (payload.exp * 1000) < Date.now();
      } catch {
        return true;
      }
    };

    // Refresh token if expired or missing
    if (!session?.access_token || isExpired(session.access_token)) {
      const { data: refreshed } = await supabase.auth.refreshSession();
      session = refreshed?.session;
    }

    if (!session?.access_token) return redirect('/login.html');

    // Securely validate against backend
    const API_BASE_URL = getEnvVar('API_BASE_URL') || '';
    if (!API_BASE_URL) throw new Error('[AuthGuard] Missing API_BASE_URL');

    const authCheck = await fetch(`${API_BASE_URL}/api/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (!authCheck.ok) return redirect('/login.html');

    // Resolve user identity
    let user = session.user;
    if (!user) {
      const { data: { user: fallbackUser }, error } = await supabase.auth.getUser();
      user = fallbackUser;
    }

    if (!user) return redirect('/login.html');

    // Pull internal user record
    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();

    if (!userData || userErr) return redirect('/login.html');
    if (!userData.setup_complete) return redirect('/play.html');
    if (requireAdmin && userData.is_admin !== true) return redirect('/overview.html');

    // Begin auto-refresh and store user context
    startSessionRefresh();
    window.user = { id: user.id, is_admin: userData.is_admin };

    if (requireAdmin) document.documentElement.style.display = '';

    // Preload progression data
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
    redirect('/login.html');
  } finally {
    document.documentElement.style.display = '';
  }
})();

// Secure redirect: atomic with hard-stop
function redirect(path) {
  window.location.replace(path);
  throw new Error(`[AuthGuard] Redirecting to ${path}`);
}
