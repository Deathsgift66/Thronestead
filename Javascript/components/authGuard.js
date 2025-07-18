// Project: Thronestead©
// File: authGuard.js
// Version: 1.7.2025.07.18
// Author: Deathsgift66 (Next-Gen Hardened Certified)
// Description: Absolute access gate with full Supabase/backend auth, session validation, admin guard, hardened redirects, timeout handling, and error management.

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
  document.documentElement.style.visibility = 'hidden';
}

(async function authGuard() {
  if (PUBLIC_PATHS.has(pathname)) return;

  try {
    const session = await getValidSession();
    if (!session?.access_token) return redirect('/login.html');

    const API_BASE_URL = getEnvVar('API_BASE_URL');
    if (!API_BASE_URL) {
      renderFatalError('[AuthGuard] Missing API_BASE_URL');
      return;
    }

    const authCheck = await fetchWithTimeout(`${API_BASE_URL}/api/me`, {
      headers: { 'Authorization': `Bearer ${session.access_token}` },
      credentials: 'include',
    }, 5000);

    if (!authCheck.ok || [401, 403].includes(authCheck.status)) {
      console.warn(`[AuthGuard] Backend auth failed: ${authCheck.status}`);
      return redirect('/login.html');
    }

    const user = session.user || (await supabase.auth.getUser()).data.user;
    if (!user) {
      console.warn('[AuthGuard] User retrieval failed');
      return redirect('/login.html');
    }

    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();

    if (userErr || !userData) {
      console.warn('[AuthGuard] Supabase user data fetch error:', userErr);
      return redirect('/login.html');
    }

    if (!userData.setup_complete) {
      console.info('[AuthGuard] Incomplete profile; redirecting to /play.html');
      return redirect('/play.html');
    }

    if (requireAdmin && !userData.is_admin) {
      console.warn('[AuthGuard] Unauthorized admin access attempt');
      return redirect('/overview.html');
    }

    window.user = Object.freeze({ id: user.id, is_admin: userData.is_admin });

    startSessionRefresh();

    try {
      loadPlayerProgressionFromStorage();
      if (!window.playerProgression) {
        await fetchAndStorePlayerProgression(user.id);
      }
    } catch (e) {
      console.warn('[AuthGuard] Player progression error:', e);
    }

    console.info('[AuthGuard] Authentication successful:', user.id);

  } catch (err) {
    console.error('[AuthGuard] Fatal authentication error:', err);
    redirect('/login.html');
  } finally {
    document.documentElement.style.visibility = 'visible';
  }
})();

// Hardened Helpers
function redirect(path) {
  if (!ALLOWED_REDIRECTS.has(path)) {
    console.error(`[AuthGuard] Invalid redirect path: ${path}`);
    path = '/login.html';
  }
  document.documentElement.style.visibility = 'hidden';
  window.location.replace(path);
}

function decodeJwt(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload.padEnd(payload.length + (4 - payload.length % 4) % 4, '=')));
  } catch (e) {
    console.warn('[AuthGuard] JWT decode error:', e);
    return null;
  }
}

function isExpired(token) {
  const decoded = decodeJwt(token);
  return !decoded || decoded.exp * 1000 < Date.now();
}

async function getValidSession() {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token && !isExpired(session.access_token)) return session;

  const { data: refreshed } = await supabase.auth.refreshSession();
  return refreshed?.session && !isExpired(refreshed.session.access_token) ? refreshed.session : null;
}

async function fetchWithTimeout(resource, options = {}, timeoutMs = 5000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(resource, { ...options, signal: controller.signal });
  } catch (err) {
    console.error('[AuthGuard] Fetch error/timeout:', err);
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

function renderFatalError(message) {
  document.body.innerHTML = `<div style="padding:50px;font-family:sans-serif;text-align:center;">
    <h1 style="color:red;">Configuration Error</h1>
    <p>${message}. Refresh or contact support.</p>
  </div>`;
  console.error(message);
}
