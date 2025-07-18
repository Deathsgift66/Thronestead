// Project: Thronestead©
// File: authGuard.js
// Version: 1.6.2025.07.18
// Author: Deathsgift66 (Next-Gen Hardened Certified)

// Absolute access gate. Supabase & backend auth, session checks, admin guards, hardened redirects.

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
      renderFatalError('[AuthGuard] Missing API_BASE_URL');
      return;
    }

    const authCheck = await fetchWithTimeout(`${API_BASE_URL}/api/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    }, 5000);

    if (!authCheck.ok || [401, 403].includes(authCheck.status)) {
      console.warn(`[AuthGuard] Backend auth failed with status: ${authCheck.status}`);
      return redirect('/login.html');
    }

    let user = session.user;
    if (!user) {
      const { data: { user: fallbackUser }, error } = await supabase.auth.getUser();
      if (error || !fallbackUser) {
        console.warn('[AuthGuard] Supabase fallback user fetch failed:', error);
        return redirect('/login.html');
      }
      user = fallbackUser;
    }

    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();

    if (userErr || !userData) {
      console.warn('[AuthGuard] User data fetch failed:', userErr);
      return redirect('/login.html');
    }

    if (!userData.setup_complete) {
      console.info('[AuthGuard] Profile incomplete, redirecting to /play.html');
      return redirect('/play.html');
    }

    if (requireAdmin && userData.is_admin !== true) {
      console.warn('[AuthGuard] Unauthorized admin access attempt.');
      return redirect('/overview.html');
    }

    window.user = window.user || Object.freeze({ id: user.id, is_admin: userData.is_admin });

    startSessionRefresh();

    try {
      loadPlayerProgressionFromStorage();
      if (!window.playerProgression) {
        await fetchAndStorePlayerProgression(user.id);
      }
    } catch (e) {
      console.warn('[AuthGuard] Player progression load failed:', e);
    }

    console.info('[AuthGuard] Authentication successful:', user.id);

  } catch (err) {
    console.error('[AuthGuard] Fatal error:', err);
    redirect('/login.html');
  } finally {
    document.documentElement.style.display = '';
  }
})();

// Hardened Helpers
function redirect(path) {
  if (!ALLOWED_REDIRECTS.has(path)) {
    console.error(`[AuthGuard] Invalid redirect attempt: ${path}`);
    path = '/login.html';
  }
  document.documentElement.style.display = 'none';
  window.location.replace(path);
}

function decodeJwt(token) {
  try {
    const payload = token.split('.')[1];
    if (!payload) throw new Error('Malformed JWT');
    const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);
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
    console.error('[AuthGuard] Fetch timeout/error:', err);
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

function renderFatalError(message) {
  document.body.innerHTML = `<div style="padding:50px;font-family:sans-serif;text-align:center;">
    <h1 style="color:red;">Configuration Error</h1>
    <p>${message}. Please refresh or contact support.</p>
  </div>`;
  console.error(message);
}
