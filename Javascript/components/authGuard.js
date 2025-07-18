// Project: Thronestead©
// File: authGuard.js
// Version: 1.9.2025.07.18
// Author: Deathsgift66 (Next-Gen Hardened Certified)
// Description: Absolute access gate with comprehensive Supabase/backend auth, session validation, admin guard, robust redirects, timeout handling, explicit CORS handling, and meticulous error management.

'use strict';

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

const AUTH_HIDDEN_CLASS = 'auth-hidden';

// Hardened visual shield management
function addAuthHidden() {
  if (!document.documentElement.classList.contains(AUTH_HIDDEN_CLASS)) {
    document.documentElement.classList.add(AUTH_HIDDEN_CLASS);
  }
}

function removeAuthHidden() {
  if (document.documentElement.classList.contains(AUTH_HIDDEN_CLASS)) {
    document.documentElement.classList.remove(AUTH_HIDDEN_CLASS);
  }
}

// Initial shield only on protected pages
if (!PUBLIC_PATHS.has(pathname)) {
  addAuthHidden();
}

// Wait for DOM ready to prevent race conditions
document.addEventListener('DOMContentLoaded', () => {
  (async function authGuard() {
    if (PUBLIC_PATHS.has(pathname)) {
      removeAuthHidden();
      return;
    }

    try {
      const session = await getValidSession();
      if (!session?.access_token) {
        console.warn('[AuthGuard] No valid access token found');
        return redirect('/login.html');
      }

      const API_BASE_URL = getEnvVar('API_BASE_URL');
      if (!API_BASE_URL) {
        return renderFatalError('[AuthGuard] Missing API_BASE_URL');
      }

      const authCheck = await fetchWithTimeout(`${API_BASE_URL}/api/me`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` },
        credentials: 'include',
        mode: 'cors',
        cache: 'no-store',
      }, 5000);

      if (!authCheck.ok || [401, 403].includes(authCheck.status)) {
        console.warn(`[AuthGuard] Backend auth failed with status: ${authCheck.status}`);
        return redirect('/login.html');
      }

      const user = session.user || (await supabase.auth.getUser())?.data?.user;
      if (!user?.id) {
        console.warn('[AuthGuard] Failed to retrieve user from session or Supabase');
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
        console.info('[AuthGuard] User setup incomplete; redirecting to /play.html');
        return redirect('/play.html');
      }

      if (requireAdmin && !userData.is_admin) {
        console.warn('[AuthGuard] Admin required but user is not admin; redirecting to /overview.html');
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
        console.warn('[AuthGuard] Player progression load error:', e);
      }

      console.info('[AuthGuard] Authentication succeeded for user:', user.id);
    } catch (err) {
      console.error('[AuthGuard] Fatal authentication error:', err);
      return redirect('/login.html');
    } finally {
      removeAuthHidden();
    }
  })();
});

// Redirect with strict path enforcement and visual shielding
function redirect(path) {
  if (!ALLOWED_REDIRECTS.has(path)) {
    console.error(`[AuthGuard] Attempted redirect to invalid path: ${path}`);
    path = '/login.html';
  }
  addAuthHidden();
  // Use replace to avoid back button going back to protected page
  window.location.replace(path);
}

// Valid session getter with refresh and expiration check
async function getValidSession() {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token && !isExpired(session.access_token)) return session;

  const { data: refreshed } = await supabase.auth.refreshSession();
  if (refreshed?.session && !isExpired(refreshed.session.access_token)) {
    return refreshed.session;
  }
  return null;
}

// Decode JWT payload safely (supports URL-safe base64)
function decodeJwt(token) {
  try {
    let payload = token.split('.')[1];
    if (!payload) throw new Error('Invalid JWT format');

    // Replace URL-safe chars for base64 decoding
    payload = payload.replace(/-/g, '+').replace(/_/g, '/');
    // Pad string for proper base64 decoding
    const padLength = (4 - (payload.length % 4)) % 4;
    payload += '='.repeat(padLength);

    return JSON.parse(atob(payload));
  } catch (e) {
    console.warn('[AuthGuard] JWT decode error:', e);
    return null;
  }
}

// Check if JWT token is expired (strict check)
function isExpired(token) {
  const decoded = decodeJwt(token);
  if (!decoded || typeof decoded.exp !== 'number') return true;
  return decoded.exp * 1000 < Date.now();
}

// Fetch with timeout and explicit abort error handling
async function fetchWithTimeout(resource, options = {}, timeoutMs = 5000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(resource, { ...options, signal: controller.signal });
    return response;
  } catch (err) {
    if (err.name === 'AbortError') {
      console.error('[AuthGuard] Fetch aborted due to timeout');
    } else {
      console.error('[AuthGuard] Fetch error:', err);
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

// Render a blocking fatal error message (with visibility reset)
function renderFatalError(message) {
  document.body.innerHTML = `
    <div style="padding:50px; font-family:sans-serif; text-align:center;">
      <h1 style="color:red;">Configuration Error</h1>
      <p>${message}. Please refresh or contact support.</p>
    </div>`;
  removeAuthHidden();
  console.error(message);
}
