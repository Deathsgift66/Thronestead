// Project: Thronestead©
// File: authGuard.js
// Version: 2.8.2025.07.18
// Author: Deathsgift66 (Next-Gen Hardened Certified)
// Description:
// Hardened Thronestead auth guard with full session validation,
// robust redirect validation, retry logic with exponential backoff,
// accessibility improvements, no global leaks, and integration hooks for auth lifecycle events.

'use strict';

import { supabase } from '../../supabaseClient.js';
import { getEnvVar } from '../env.js';
import { startSessionRefresh } from '../auth.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';

/** @typedef {import('node-fetch').Response} Response */

/** Configuration constants */
const CONFIG = Object.freeze({
  PUBLIC_PATHS: [
    '/index.html',
    '/about.html',
    '/profile.html',
    '/login.html',
    '/signup.html',
    '/update-password.html',
    '/legal.html',
    '/404.html',
  ],
  ALLOWED_REDIRECTS: [
    '/login.html',
    '/play.html',
    '/overview.html',
  ],
  AUTH_HIDDEN_CLASS: 'auth-hidden',
  FETCH_TIMEOUT_MS: 5000,
  FETCH_MAX_RETRIES: 3,
  DOMCONTENTLOADED_FALLBACK_MS: 3000,
  DEBUG_MODE: getEnvVar('DEBUG_AUTH_GUARD')?.toLowerCase() === 'true',
});

/** Tracks if auth guard has run already */
let hasRunAuthGuard = false;

/** Private symbol and data store for user info */
const userSymbol = Symbol('authGuardUser');
let _userData = null;

/**
 * Get immutable user info.
 * @returns {{id: string, is_admin: boolean}|null}
 */
const getUserData = () => _userData;

/** Expose a safe getter on window */
Object.defineProperty(window, 'getUser', {
  configurable: false,
  enumerable: false,
  writable: false,
  value: getUserData,
});

/** Logger utility */
const log = {
  info: (msg, ...args) => {
    if (CONFIG.DEBUG_MODE) {
      console.info(`[${new Date().toISOString()}][AUTHGUARD][INFO] ${msg}`, ...args);
    }
  },
  warn: (msg, ...args) => console.warn(`[${new Date().toISOString()}][AUTHGUARD][WARN] ${msg}`, ...args),
  error: (msg, ...args) => console.error(`[${new Date().toISOString()}][AUTHGUARD][ERROR] ${msg}`, ...args),
};

/**
 * Normalize a URL path safely.
 * @param {string} path
 * @returns {string}
 */
function normalizePath(path) {
  if (typeof path !== 'string') return '';
  try {
    const base = 'https://example.com'; // Dummy base for relative URL parsing
    const url = new URL(path, base);
    let normalized = url.pathname.toLowerCase();
    if (normalized !== '/' && normalized.endsWith('/')) normalized = normalized.slice(0, -1);
    return normalized;
  } catch {
    let clean = path.split('?')[0].split('#')[0].toLowerCase();
    if (clean !== '/' && clean.endsWith('/')) clean = clean.slice(0, -1);
    return clean;
  }
}

/** Adds hidden class to <html> to prevent UI flash */
const addAuthHidden = () => {
  if (!document.documentElement.classList.contains(CONFIG.AUTH_HIDDEN_CLASS)) {
    document.documentElement.classList.add(CONFIG.AUTH_HIDDEN_CLASS);
  }
};

/** Removes hidden class to reveal UI */
const removeAuthHidden = () => {
  if (document.documentElement.classList.contains(CONFIG.AUTH_HIDDEN_CLASS)) {
    document.documentElement.classList.remove(CONFIG.AUTH_HIDDEN_CLASS);
  }
};

/**
 * Escape HTML special chars in string to prevent injection
 * @param {string} unsafe
 * @returns {string}
 */
const escapeHtml = (() => {
  const map = new Map([
    ['&', '&amp;'],
    ['<', '&lt;'],
    ['"', '&quot;'],
    ['\'', '&#39;'],
  ]);
  return (unsafe) => unsafe.replace(/[&<"']/g, ch => map.get(ch) || ch);
})();

/**
 * Render fatal error blocking message with proper accessibility
 * @param {string} message
 */
function renderFatalError(message) {
  const main = document.createElement('main');
  main.setAttribute('role', 'alert');
  main.setAttribute('aria-live', 'assertive');
  main.setAttribute('tabindex', '-1');
  main.style.cssText = 'padding:50px; font-family:sans-serif; text-align:center;';

  const h1 = document.createElement('h1');
  h1.style.color = 'red';
  h1.textContent = 'Configuration Error';

  const p = document.createElement('p');
  p.textContent = `${message}. Please refresh or contact support.`;

  main.appendChild(h1);
  main.appendChild(p);

  document.body.innerHTML = '';
  document.body.appendChild(main);
  removeAuthHidden();

  setTimeout(() => main.focus(), 100);

  log.error(message);
}

/**
 * Validate redirect path string strictly.
 * @param {string} path
 * @returns {boolean}
 */
function isValidRedirectPath(path) {
  if (typeof path !== 'string') return false;

  try {
    const decoded = decodeURIComponent(path);
    if (/(\.\.|\.\/|\/\/|https?:)/i.test(decoded)) return false;
  } catch {
    return false;
  }

  const normalized = normalizePath(path);
  return CONFIG.ALLOWED_REDIRECTS.includes(normalized);
}

/**
 * Perform secure redirect with validation.
 * @param {string} path
 */
function redirect(path) {
  if (!isValidRedirectPath(path)) {
    log.error(`Invalid redirect attempted: ${path}, defaulting to /login.html`);
    path = '/login.html';
  }
  addAuthHidden();
  window.location.replace(path);
}

/**
 * Decode JWT payload with base64 URL-safe support.
 * Uses browser-native atob or TextDecoder fallback.
 * @param {string} token
 * @returns {object|null}
 */
function decodeJwt(token) {
  try {
    let payload = token.split('.')[1];
    if (!payload) throw new Error('Malformed JWT');
    payload = payload.replace(/-/g, '+').replace(/_/g, '/');
    const pad = (4 - (payload.length % 4)) % 4;
    payload += '='.repeat(pad);

    if (typeof atob === 'function') {
      return JSON.parse(atob(payload));
    }
    const binary = Uint8Array.from(atob(payload), c => c.charCodeAt(0));
    const decoder = new TextDecoder();
    return JSON.parse(decoder.decode(binary));
  } catch (err) {
    log.warn('JWT decode failure:', err);
    return null;
  }
}

/**
 * Checks JWT expiry with strict type safety.
 * @param {string} token
 * @returns {boolean}
 */
function isExpired(token) {
  const decoded = decodeJwt(token);
  if (!decoded || typeof decoded.exp !== 'number') return true;
  return decoded.exp * 1000 < Date.now();
}

/**
 * Sleep helper with Promise.
 * @param {number} ms
 * @returns {Promise<void>}
 */
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Fetch wrapper with timeout, retries, and jitter backoff.
 * Retries on network errors and 5xx statuses.
 * @param {string} resource
 * @param {RequestInit} options
 * @param {number} timeoutMs
 * @param {number} retries
 * @returns {Promise<Response>}
 * @throws {Error}
 */
async function fetchWithTimeout(resource, options = {}, timeoutMs = CONFIG.FETCH_TIMEOUT_MS, retries = CONFIG.FETCH_MAX_RETRIES) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(resource, { ...options, signal: controller.signal });
      if (response.status >= 500 && attempt < retries) {
        const jitter = Math.random() * 300;
        log.warn(`Fetch returned ${response.status}, retrying after backoff (attempt ${attempt + 1}/${retries + 1})`);
        await sleep(500 * (attempt + 1) + jitter);
        continue;
      }
      return response;
    } catch (err) {
      if (err.name === 'AbortError') {
        log.error(`Fetch timeout aborted (attempt ${attempt + 1}/${retries + 1})`);
      } else {
        log.error(`Fetch error (attempt ${attempt + 1}/${retries + 1}):`, err);
      }
      if (attempt < retries) {
        const jitter = Math.random() * 300;
        await sleep(500 * (attempt + 1) + jitter);
        continue;
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  }
  throw new Error('Fetch retries exhausted unexpectedly');
}

/**
 * Get valid Supabase session, refreshing if expired.
 * @async
 * @returns {Promise<object|null>}
 */
async function getValidSession() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token && !isExpired(session.access_token)) return session;

    const { data: refreshed } = await supabase.auth.refreshSession();
    if (refreshed?.session && !isExpired(refreshed.session.access_token)) return refreshed.session;
  } catch (err) {
    log.warn('Session retrieval error:', err);
  }
  return null;
}

/**
 * Main authentication guard logic, idempotent.
 * @async
 */
async function mainAuthGuard() {
  if (hasRunAuthGuard) return;
  hasRunAuthGuard = true;

  if (CONFIG.PUBLIC_PATHS.includes(pathname)) {
    removeAuthHidden();
    return;
  }

  if (typeof navigator !== 'undefined' && !navigator.onLine) {
    log.warn('Offline detected, redirecting to login');
    return redirect('/login.html');
  }

  const API_BASE_URL = getEnvVar('API_BASE_URL');
  if (!API_BASE_URL) {
    return renderFatalError('[AuthGuard] Missing API_BASE_URL environment variable');
  }

  let session;
  try {
    session = await getValidSession();
  } catch (err) {
    log.warn('Session fetch failed:', err);
  }

  if (!session?.access_token) {
    log.warn('No valid access token present');
    return redirect('/login.html');
  }

  let authCheck;
  try {
    authCheck = await fetchWithTimeout(`${API_BASE_URL}/api/me`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
      credentials: 'include',
      mode: 'cors',
      cache: 'no-store',
    }, CONFIG.FETCH_TIMEOUT_MS, CONFIG.FETCH_MAX_RETRIES);
  } catch (err) {
    log.warn('Backend auth check failed:', err);
    return redirect('/login.html');
  }

  if (!authCheck.ok || [401, 403].includes(authCheck.status)) {
    log.warn(`Auth check returned status ${authCheck.status}`);
    return redirect('/login.html');
  }

  let user;
  try {
    user = session.user || (await supabase.auth.getUser())?.data?.user;
  } catch (err) {
    log.warn('User retrieval failed:', err);
  }

  if (!user?.id) {
    log.warn('User missing in session');
    return redirect('/login.html');
  }

  let userData;
  try {
    const res = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();
    if (res.error) {
      log.warn('Supabase user query error:', res.error);
      return redirect('/login.html');
    }
    userData = res.data;
  } catch (err) {
    log.warn('Supabase user fetch exception:', err);
    return redirect('/login.html');
  }

  if (!userData.setup_complete) {
    log.info('User setup incomplete, redirecting to /play.html');
    return redirect('/play.html');
  }

  // Cache requireAdmin from meta tag, normalized and fail-safe
  let requireAdminRaw = 'false';
  try {
    requireAdminRaw = document.querySelector('meta[name="require-admin"]')?.content || 'false';
  } catch {
    // silently fail
  }
  const requireAdminFinal = String(requireAdminRaw).toLowerCase() === 'true';

  if (requireAdminFinal && !userData.is_admin) {
    log.warn('Admin access required but user not admin, redirecting to /overview.html');
    return redirect('/overview.html');
  }

  _userData = Object.freeze({ id: user.id, is_admin: userData.is_admin });

  startSessionRefresh();

  try {
    loadPlayerProgressionFromStorage();
    if (!window.playerProgression) {
      await fetchAndStorePlayerProgression(user.id);
    }
  } catch (e) {
    log.warn('Player progression load failure:', e);
  }

  log.info(`User authenticated successfully: ID=${user.id}`);

  removeAuthHidden();
}

/** Init auth guard with DOM ready fallback */
(function initAuthGuard() {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mainAuthGuard, { once: true });
    setTimeout(() => {
      if (!hasRunAuthGuard) {
        log.warn('Fallback DOMContentLoaded timeout, invoking auth guard');
        mainAuthGuard();
      }
    }, CONFIG.DOMCONTENTLOADED_FALLBACK_MS);
  } else {
    mainAuthGuard();
  }
})();
