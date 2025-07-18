// CSRF Token Utilities (Next-Gen Hardened v4)
// Author: Thronestead Security Suite
// Version: 4.0.2025.07.18

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_META_KEY = 'csrf_token_ts';
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_EXPIRY_MS = 6 * 60 * 60 * 1000; // 6 hours
const CSRF_CHANNEL = 'csrf-sync';

let csrfChannel = null;
let now = () => Date.now(); // injectable for testing

/**
 * Initializes and returns a CSRF token, generating if needed.
 */
export function initCsrf() {
  ensureChannel();
  const stored = getStoredToken();
  if (stored && !isExpired(stored.timestamp)) return stored.token;
  return rotateCsrfToken();
}

/**
 * Rotates CSRF token forcefully, syncing across tabs.
 */
export function rotateCsrfToken() {
  const token = generateToken();
  storeToken(token);
  broadcastToken(token);
  return token;
}

/**
 * Retrieves current valid CSRF token or null.
 */
export function getCsrfToken() {
  const stored = getStoredToken();
  return stored && !isExpired(stored.timestamp) ? stored.token : null;
}

/**
 * Injects a custom time function (for testing).
 */
export function injectNow(fn) {
  if (typeof fn === 'function') now = fn;
}

/* ===== INTERNAL UTILITIES ===== */

/**
 * Retrieves token and timestamp from sessionStorage.
 */
function getStoredToken() {
  try {
    const token = sessionStorage.getItem(CSRF_TOKEN_KEY);
    const ts = Number(sessionStorage.getItem(CSRF_META_KEY));
    if (!isValidToken(token)) return null;
    return { token, timestamp: isNaN(ts) ? 0 : ts };
  } catch (err) {
    console.warn('[CSRF] Failed to read sessionStorage:', err);
    return null;
  }
}

/**
 * Stores token into sessionStorage and secure cookie.
 */
function storeToken(token) {
  const timestamp = now();
  try {
    sessionStorage.setItem(CSRF_TOKEN_KEY, token);
    sessionStorage.setItem(CSRF_META_KEY, timestamp.toString());
  } catch (err) {
    console.warn('[CSRF] Failed to write to sessionStorage:', err);
  }
  setCookie(CSRF_COOKIE_NAME, token, timestamp + CSRF_EXPIRY_MS);
}

/**
 * Checks if a token is expired.
 */
function isExpired(ts) {
  return now() - ts > CSRF_EXPIRY_MS;
}

/**
 * Sets a secure cookie with optional expiration.
 */
function setCookie(name, value, expiresAt) {
  if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
    console.warn('[CSRF] Insecure context — Secure cookies may be ignored.');
  }
  const expires = expiresAt ? `; Expires=${new Date(expiresAt).toUTCString()}` : '';
  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; Path=/; Secure; SameSite=Strict${expires}`;
}

/**
 * Generates a secure UUID token or fallback.
 */
function generateToken() {
  if (crypto?.randomUUID) return crypto.randomUUID();
  if (crypto?.getRandomValues) {
    const arr = new Uint8Array(16);
    crypto.getRandomValues(arr);
    return [...arr].map(b => b.toString(16).padStart(2, '0')).join('');
  }
  return `tkn-${now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

/**
 * Checks if token is valid format.
 */
function isValidToken(token) {
  return typeof token === 'string' && /^[\w-]{16,}$/.test(token);
}

/**
 * Broadcasts new token across tabs.
 */
function broadcastToken(token) {
  if (csrfChannel) {
    csrfChannel.postMessage({ type: 'rotate', token });
  }
}

/**
 * Initializes BroadcastChannel if supported.
 */
function ensureChannel() {
  if (!csrfChannel && 'BroadcastChannel' in window) {
    csrfChannel = new BroadcastChannel(CSRF_CHANNEL);
    csrfChannel.onmessage = (e) => {
      if (e.data?.type === 'rotate' && isValidToken(e.data.token)) {
        const current = getCsrfToken();
        if (!current || current !== e.data.token) {
          storeToken(e.data.token);
        }
      }
    };
  }
}
