// Project Name: Thronestead©
// File Name: auth.js
// Version 6.18.2025.22.00
// Developer: Codex
// Shared helper for retrieving authenticated user and headers

import { supabase } from '../supabaseClient.js';

let cachedAuth = null;

/**
 * Retrieve stored auth token and user info from browser storage.
 * @returns {{token: string|null, user: object|null}}
 */
export function getStoredAuth() {
  const token = sessionStorage.getItem('authToken') ||
    localStorage.getItem('authToken');
  const userStr = sessionStorage.getItem('currentUser') ||
    localStorage.getItem('currentUser');
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
  sessionStorage.removeItem('authToken');
  sessionStorage.removeItem('currentUser');
  localStorage.removeItem('authToken');
  localStorage.removeItem('currentUser');
  resetAuthCache();
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
    const storage = localStorage.getItem('authToken') ? localStorage : sessionStorage;
    const alt = storage === localStorage ? sessionStorage : localStorage;
    storage.setItem('authToken', token);
    storage.setItem('currentUser', JSON.stringify(user));
    alt.removeItem('authToken');
    alt.removeItem('currentUser');

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
  refreshIntervalId = setInterval(refreshSessionAndStore, intervalMs);
}

export function stopSessionRefresh() {
  if (refreshIntervalId) {
    clearInterval(refreshIntervalId);
    refreshIntervalId = null;
  }
}

