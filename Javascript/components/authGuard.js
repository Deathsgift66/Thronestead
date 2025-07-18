// Project: Thronestead©
// File: authGuard.js
// Version: 1.4.2025.07.18
// Author: Deathsgift66 (Next-Gen Hardened Certified)

// Description:
// Absolute access gate for secure pages. Authenticates Supabase sessions,
// validates backend sessions, profile completeness, secures admin routes,
// prevents token spoofing, fetch hangs, race conditions, and visual leaks.

import { supabase } from '../../supabaseClient.js';
import { getEnvVar } from '../env.js';
import { startSessionRefresh } from '../auth.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';

const PUBLIC_PATHS = new Set([
  '/index.html',
  '/about.html',
  '/projects.html',
  '/login.html',
  '/signup.html',
  '/update-password.html',
  '/legal.html',
  '/404.html',
]);

const ALLOWED_REDIRECTS = new Set([
  '/login.html',
  '/play.html',
  '/overview.html',
]);

const pathname = window.location.pathname.split('?')[0].split('#')[0];
const requireAdmin = document.querySelector('meta[name="require-admin"]')?.content === 'true';

// Initial visual shield
if (!PUBLIC_PATHS.has(pathname)) {
  document.documentElement.style.display = 'none';
}

(async function authGuard() {
  if (PUBLIC_PATHS.has(pathname)) return;

  try {
    const session = await getValidSession();
    if (!session?.access_token) return redirect('/login.html');

    const API_BASE_URL = getEnvVar('API_BASE_URL');
    if (!API_BASE_URL) {
      alert('[Thronestead AuthGuard Error] Server misconfiguration. Try refreshing.');
      throw new Error('[AuthGuard] Missing API_BASE_URL');
    }

    const authCheck = await fetchWithTimeout(`${API_BASE_URL}/api/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    }, 5000);

    if (!authCheck.ok) return redirect('/login.html');

    let user = session.user;
    if (!user) {
      const { data: { user: fallbackUser }, error: fallbackErr } = await supabase.auth.getUser();
      if (fallbackErr || !fallbackUser) return redirect('/login.html');
      user = fallbackUser;
    }

    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();

    if (!userData || userErr) return redirect('/login.html');
    if (!userData.setup_complete) return redirect('/play.html');
    if (requireAdmin && userData.is_admin !== true) return redirect('/overview.html');

    if (window.user) {
      console.warn('[AuthGuard] window.user already defined');
    } else {
      window.user = Object.freeze({ id: user.id, is_admin: userData.is_admin });
    }

    startSessionRefresh();

    try {
      loadPlayerProgressionFromStorage();
      if (!window.playerProgression) {
        await fetchAndStorePlayerProgression(user.id);
      }
    } catch (e) {
      console.warn('[AuthGuard] Progression load failed:', e);
    }

  } catch (err) {
    console.error('[AuthGuard] Fatal error:', err);
    redirect('/login.html');
  } finally {
    document.documentElement.style.display = '';
  }
})();

// ===============================
// Hardened Helpers
// ===============================

function redirect(path) {
  if (!ALLOWED_REDIRECTS.has(path)) {
    console.error(`[AuthGuard] Invalid redirect attempted: ${path}`);
    path = '/login.html';
  }
  document.documentElement.style.display = 'none';
  window.location.replace(path);
  throw new Error(`[AuthGuard] Redirecting to ${path}`);
}

function decodeJwt(token) {
  try {
    const payload = token.split('.')[1];
    const paddedPayload = payload.padEnd(payload.length + (4 - payload.length % 4) % 4, '=');
    return JSON.parse(atob(paddedPayload));
  } catch (e) {
    console.warn('[AuthGuard] decodeJwt failed:', e);
    return null;
  }
}

function isExpired(token) {
  const decoded = decodeJwt(token);
  return !decoded || decoded.exp * 1000 < Date.now();
}

async function getValidSession() {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session?.access_token || isExpired(session.access_token)) {
    const { data: refreshed } = await supabase.auth.refreshSession();
    if (refreshed?.session && !isExpired(refreshed.session.access_token)) {
      return refreshed.session;
    }

    const retry = await supabase.auth.getSession();
    if (!retry?.data?.session?.access_token || isExpired(retry.data.session.access_token)) {
      await supabase.auth.signOut();
      return null;
    }

    return retry.data.session;
  }

  return session;
}

async function fetchWithTimeout(resource, options = {}, timeoutMs = 5000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(resource, { ...options, signal: controller.signal });
  } catch (err) {
    console.error('[AuthGuard] Fetch timeout/error:', err);
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}
