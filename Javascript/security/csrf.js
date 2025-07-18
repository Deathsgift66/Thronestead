// CSRF Token Utilities (Next-Gen Hardened)
// Author: Thronestead Security Suite
// Version: 2.0.2025.07.18

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_EXPIRY_MS = 6 * 60 * 60 * 1000; // 6 hours
const CSRF_META_KEY = 'csrf_token_ts';     // optional timestamp for internal expiry

/**
 * Initializes and returns a CSRF token (only if valid or freshly generated).
 */
export function initCsrf() {
  const existing = getStoredToken();
  if (existing && !isExpired(existing.timestamp)) {
    return existing.token;
  }
  const token = generateToken();
  storeToken(token);
  return token;
}

/**
 * Rotates the CSRF token and returns the new token.
 */
export function rotateCsrfToken() {
  const token = generateToken();
  storeToken(token);
  return token;
}

/**
 * Gets the valid current CSRF token, or null if invalid or expired.
 */
export function getCsrfToken() {
  const data = getStoredToken();
  return data && !isExpired(data.timestamp) ? data.token : null;
}

/**
 * Internal: stores token + timestamp.
 */
function storeToken(token) {
  const timestamp = Date.now();
  sessionStorage.setItem(CSRF_TOKEN_KEY, token);
  sessionStorage.setItem(CSRF_META_KEY, timestamp.toString());
  setCookie(CSRF_COOKIE_NAME, token, timestamp + CSRF_EXPIRY_MS);
}

/**
 * Internal: retrieves token and timestamp from sessionStorage.
 */
function getStoredToken() {
  const token = sessionStorage.getItem(CSRF_TOKEN_KEY);
  const ts = parseInt(sessionStorage.getItem(CSRF_META_KEY), 10);
  if (!isValidToken(token)) return null;
  return { token, timestamp: isNaN(ts) ? 0 : ts };
}

/**
 * Determines if a timestamp is expired.
 */
function isExpired(timestamp) {
  return Date.now() - timestamp > CSRF_EXPIRY_MS;
}

/**
 * Generates UUIDv4 or strong fallback if crypto is not available.
 */
function generateToken() {
  if (crypto?.randomUUID) return crypto.randomUUID();
  if (crypto?.getRandomValues) {
    const arr = new Uint8Array(16);
    crypto.getRandomValues(arr);
    return [...arr].map(b => b.toString(16).padStart(2, '0')).join('');
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

/**
 * Token format: 16+ chars, alphanumeric+hyphen
 */
function isValidToken(token) {
  return typeof token === 'string' && /^[\w-]{16,}$/.test(token);
}

/**
 * Sets secure cookie with optional expiration (used by server for double-submit).
 */
function setCookie(name, value, expiresAt) {
  const expires = expiresAt ? `; Expires=${new Date(expiresAt).toUTCString()}` : '';
  document.cookie = `${name}=${value}; Path=/; Secure; SameSite=Strict${expires}`;
}
