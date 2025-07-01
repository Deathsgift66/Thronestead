// Project Name: Thronestead©
// File Name: auth.js
// Version 7.1.2025.00.00
// Developer: Codex (Hardened Build)

import { supabase } from '../supabaseClient.js';

/**
 * Retrieve stored auth token and user from local/session storage.
 */
export function getStoredAuth() {
  const token = localStorage.getItem('authToken');
  const userStr = sessionStorage.getItem('currentUser') || localStorage.getItem('currentUser');
  let user = null;

  if (userStr) {
    try {
      user = JSON.parse(userStr);
    } catch (err) {
      console.warn('⚠️ Failed to parse stored user:', err);
      user = null;
    }
  }

  return { token, user };
}

/**
 * Cache auth for page lifetime (performance).
 */

/**
 * Supabase user/session fetch with defensive guards.
 */
export async function getAuth() {
  try {
    const [{ data: { user } }, { data: { session } }] = await Promise.all([
      supabase.auth.getUser(),
      supabase.auth.getSession()
    ]);
    if (!user || !session) throw new Error('Unauthorized');
    return { user, session };
  } catch (err) {
    console.error('❌ Failed to retrieve auth:', err);
    throw new Error('Unauthorized');
  }
}

/**
 * Build authenticated headers.
 */
export async function authHeaders() {
  const { user, session } = await getAuth();
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'X-User-ID': user.id
  };
}

/**
 * Clear cache.
 */
export function resetAuthCache() {}

/**
 * Clear session + cross-tab logout.
 */
export function clearStoredAuth() {
  try {
    sessionStorage.removeItem('currentUser');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('authToken');
    localStorage.setItem('thronesteadLogout', Date.now().toString()); // broadcast logout
  } catch (err) {
    console.warn('⚠️ Failed to clear auth:', err);
  }
  resetAuthCache();
}

/**
 * Refresh Supabase session and store result.
 */
export async function refreshSessionAndStore() {
  try {
    const { data, error } = await supabase.auth.refreshSession();
    if (error || !data?.session) {
      console.warn('⚠️ Session refresh failed:', error);
      return false;
    }
    return true;
  } catch (err) {
    console.error('❌ Session refresh threw error:', err);
    return false;
  }
}

// 🔁 Periodic Session Refresh
let refreshIntervalId = null;

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
 * Check expiry, refresh if needed.
 */
export async function refreshIfExpiring(thresholdSec = 300) {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const expiresIn = session?.expires_at * 1000 - Date.now();

    if (session && expiresIn < thresholdSec * 1000) {
      console.info('🔁 Session near expiry, refreshing...');
      await refreshSessionAndStore();
    }

    await validateSessionOrLogout();
  } catch (err) {
    console.warn('⚠️ Session refresh check failed:', err);
  }
}

/**
 * Validate session by pinging backend.
 */
export async function validateSessionOrLogout() {
  const { data: { session } } = await supabase.auth.getSession();
  if (session) return true;
  clearStoredAuth();
  if (!location.pathname.endsWith('login.html')) {
    window.location.href = 'login.html';
  }
  return false;
}

// 🔄 Multi-tab logout sync
window.addEventListener('storage', e => {
  if (e.key === 'thronesteadLogout') {
    resetAuthCache();
    sessionStorage.removeItem('currentUser');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('authToken');

    if (!location.pathname.endsWith('login.html')) {
      window.location.href = 'login.html';
    }
  }
});
