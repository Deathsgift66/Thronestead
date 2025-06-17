// Project Name: Thronestead©
// File Name: auth.js
// Version 6.14.2025.20.45
// Developer: Codex
// Shared helper for retrieving authenticated user and headers

import { supabase } from './supabaseClient.js';

let cachedAuth = null;

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
  const { user, session } = await getAuth();
  return {
    'X-User-ID': user.id,
    Authorization: `Bearer ${session.access_token}`
  };
}

/**
 * Clear the cached user/session data (e.g. on logout).
 */
export function resetAuthCache() {
  cachedAuth = null;
}

