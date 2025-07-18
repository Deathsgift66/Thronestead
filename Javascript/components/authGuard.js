// Project: Thronestead©
// File: authGuard.js
// Version: 7/18/2025
// Author: Deathsgift66

import { supabase } from '../../supabaseClient.js';
import { getEnvVar } from '../env.js';
import { startSessionRefresh } from '../auth.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';

// Config flags
const requireAdmin = window.requireAdmin === true;
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

(async function authGuard() {
  if (PUBLIC_PATHS.has(pathname)) {
    return;
  }

  if (requireAdmin) {
    document.documentElement.style.display = 'none';
  }

  try {
    // Get or refresh session
    let { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      const { data: refreshed } = await supabase.auth.refreshSession();
      session = refreshed?.session;
    }

    if (!session?.access_token) {
      return redirect('/login.html');
    }

    // Server-side validation
    const API_BASE_URL = getEnvVar('API_BASE_URL');
    const authCheck = await fetch(`${API_BASE_URL}/api/me`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
      credentials: 'include',
    });
    if (!authCheck.ok) {
      return redirect('/login.html');
    }

    // Supabase user fetch
    let { data: { user }, error } = await supabase.auth.getUser();
    if (!user || error) {
      const { data: refreshed } = await supabase.auth.refreshSession();
      user = refreshed?.user;
    }

    if (!user) {
      return redirect('/login.html');
    }

    // Begin token refresh cycle
    startSessionRefresh();

    // Get internal user profile
    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();

    if (!userData || userErr) {
      return redirect('/login.html');
    }

    if (!userData.setup_complete) {
      return redirect('/play.html');
    }

    if (requireAdmin && userData.is_admin !== true) {
      return redirect('/overview.html');
    }

    // Success: expose user globally
    window.user = { id: user.id, is_admin: userData.is_admin };

    // Unhide page for admin-only views
    if (requireAdmin) {
      document.documentElement.style.display = '';
    }

    // Load progression
    loadPlayerProgressionFromStorage();
    if (!window.playerProgression) {
      await fetchAndStorePlayerProgression(user.id);
    }

  } catch (err) {
    console.error('AuthGuard error:', err);
    document.documentElement.style.display = '';
    redirect('/login.html');
  }
})();

function redirect(path) {
  window.location.href = path;
}
