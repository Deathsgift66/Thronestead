// Project Name: Thronestead©
// File Name: auth.js
// Version 6.20.2025.23.00
// Developer: Codex
// Shared helper for retrieving authenticated user and headers

import { supabase } from '../supabaseClient.js';

let cachedAuth = null;

/**
 * Retrieve stored auth token and user info from browser storage.
 * @returns {{token: string|null, user: object|null}}
 */
export function getStoredAuth() {
  const token =
    sessionStorage.getItem('authToken') || localStorage.getItem('authToken');
  const userStr =
    sessionStorage.getItem('currentUser') || localStorage.getItem('currentUser');
  let user = null;
  if (userStr) {
    try {
      user = JSON.parse(userStr);
    } catch {
      user = null;
    }
  }
  return { token, user };
}

/**
 * Manually update the cached user/session.
 * Useful after login without a page reload.
 * @param {object} user Supabase user info
 * @param {object} session Supabase session data
 */
export function setAuthCache(user, session) {
  cachedAuth = { user, session };
}

/**
 * Retrieve the current user and session from Supabase.
 * The result is cached for the lifetime of the page to avoid
 * redundant API calls.
 * @returns {Promise<{user: object, session: object}>}
 * @throws {Error} if no authenticated session is available
 */
export async function getAuth() {
  if (cachedAuth) return cachedAuth;
  const [{ data: { user } }, { data: { session } }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession()
  ]);
  if (!user || !session) throw new Error('Unauthorized');
  cachedAuth = { user, session };
  return cachedAuth;
}

/**
 * Build standard headers for authenticated API requests.
 * @returns {Promise<Record<string, string>>}
 */
export async function authHeaders() {
  const { token, user } = getStoredAuth();
  if (token && user?.id) {
    return {
      'X-User-ID': user.id,
      Authorization: `Bearer ${token}`
    };
  }

  const { user: supaUser, session } = await getAuth();
  return {
    'X-User-ID': supaUser.id,
    Authorization: `Bearer ${session.access_token}`
  };
}

/**
 * Clear the cached user/session data (e.g. on logout).
 */
export function resetAuthCache() {
  cachedAuth = null;
}

/**
 * Remove stored auth token and user information.
 */
export function clearStoredAuth() {
  sessionStorage.removeItem('currentUser');
  localStorage.removeItem('currentUser');
  sessionStorage.removeItem('authToken');
  localStorage.removeItem('authToken');
  resetAuthCache();
  // Notify other tabs to logout
  try {
    localStorage.setItem('thronesteadLogout', Date.now().toString());
  } catch {}
}

/**
 * Refresh the Supabase session and update stored credentials.
 * @returns {Promise<boolean>} True if refresh succeeded
 */
export async function refreshSessionAndStore() {
  try {
    const { data, error } = await supabase.auth.refreshSession();
    if (error || !data?.session) return false;

    const token = data.session.access_token;
    const user = data.user;
    sessionStorage.setItem('authToken', token);
    if (localStorage.getItem('currentUser')) {
      localStorage.setItem('authToken', token);
    }
    sessionStorage.setItem('currentUser', JSON.stringify(user));

    setAuthCache(user, data.session);
    return true;
  } catch {
    return false;
  }
}

let refreshIntervalId = null;

/**
 * Periodically refresh the user's session token.
 * @param {number} intervalMs Refresh interval in milliseconds
 */
export function startSessionRefresh(intervalMs = 50 * 60 * 1000) {
  if (refreshIntervalId) return;
  refreshIntervalId = setInterval(refreshIfExpiring, intervalMs);
  refreshIfExpiring();
}

export function stopSessionRefresh() {
  if (refreshIntervalId) {
    clearInterval(refreshIntervalId);
    refreshIntervalId = null;
  }
}

/**
 * Check session expiration and refresh if it is close to expiring.
 * @param {number} thresholdSec Number of seconds before expiry to trigger refresh
 */
export async function refreshIfExpiring(thresholdSec = 300) {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session && session.expires_at * 1000 - Date.now() < thresholdSec * 1000) {
      await refreshSessionAndStore();
    }
    await validateSessionOrLogout();
  } catch (err) {
    console.warn('Session refresh check failed:', err);
  }
}

/**
 * Validate the current session using the backend and logout if invalid.
 * @returns {Promise<boolean>} True if session is valid
 */
export async function validateSessionOrLogout() {
  try {
    const headers = await authHeaders();
    const res = await fetch('/api/auth/validate-session', { headers });
    if (res.status === 401) throw new Error('invalid');
    return true;
  } catch {
    clearStoredAuth();
    window.location.href = 'login.html';
    return false;
  }
}

// Listen for logout events from other tabs
window.addEventListener('storage', e => {
  if (e.key === 'thronesteadLogout') {
    resetAuthCache();
    sessionStorage.removeItem('currentUser');
    localStorage.removeItem('currentUser');
    sessionStorage.removeItem('authToken');
    localStorage.removeItem('authToken');
    if (!location.pathname.endsWith('login.html')) {
      window.location.href = 'login.html';
    }
  }
});

