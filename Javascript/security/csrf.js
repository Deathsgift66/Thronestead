// CSRF Token Utilities (Next-Gen Hardened v3)
// Author: Thronestead Security Suite
// Version: 3.0.2025.07.18

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_META_KEY = 'csrf_token_ts';
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_EXPIRY_MS = 6 * 60 * 60 * 1000; // 6 hours
const CSRF_CHANNEL = 'csrf-sync';

let csrfChannel = null;

// Allow injection of custom time function for testing
let now = () => Date.now();

/**
 * Initializes and returns a CSRF token (existing or new).
 */
export function initCsrf() {
  ensureChannel();
  const existing = getStoredToken();
  if (existing && !isExpired(existing.timestamp)) {
    return existing.token;
  }
  const token = generateToken();
  storeToken(token);
  return token;
}

/**
 * Rotates CSRF token forcefully and broadcasts change.
 */
export function rotateCsrfToken() {
  const token = generateToken();
  storeToken(token);
  return token;
}

/**
 * Gets valid token from sessionStorage or null if expired/invalid.
 */
export function getCsrfToken() {
  const data = getStoredToken();
  return data && !isExpired(data.timestamp) ? data.token : null;
}

/**
 * Sets a custom now() for testing/mocking.
 */
export function injectNow(fn) {
  if (typeof fn === 'function') now = fn;
}

/**
 * INTERNAL: Get token + timestamp from session.
 */
function getStoredToken() {
  const token = sessionStorage.getItem(CSRF_TOKEN_KEY);
  const ts = Number(sessionStorage.getItem(CSRF_META_KEY));
  if (!isValidToken(token)) return null;
  return { token, timestamp: isNaN(ts) ? 0 : ts };
}

/**
 * INTERNAL: Stores token in sessionStorage and secure cookie.
 */
function storeToken(token) {
  const timestamp = now();
  sessionStorage.setItem(CSRF_TOKEN_KEY, token);
  sessionStorage.setItem(CSRF_META_KEY, timestamp.toString());
  setCookie(CSRF_COOKIE_NAME, token, timestamp + CSRF_EXPIRY_MS);
  broadcastToken(token);
}

/**
 * INTERNAL: Checks if a token is expired.
 */
function isExpired(timestamp) {
  return now() - timestamp > CSRF_EXPIRY_MS;
}

/**
 * INTERNAL: Sets cookie with secure flags and optional expiration.
 */
function setCookie(name, value, expiresAt) {
  if (location.protocol !== 'https:') {
    console.warn(`[CSRF] Insecure context: Secure cookies may not work over HTTP.`);
  }
  const expires = expiresAt ? `; Expires=${new Date(expiresAt).toUTCString()}` : '';
  document.cookie = `${name}=${value}; Path=/; Secure; SameSite=Strict${expires}`;
}

/**
 * INTERNAL: Generate UUID or fallback secure token.
 */
function generateToken() {
  if (crypto?.randomUUID) return crypto.randomUUID();
  if (crypto?.getRandomValues) {
    const arr = new Uint8Array(16);
    crypto.getRandomValues(arr);
    return [...arr].map(b => b.toString(16).padStart(2, '0')).join('');
  }
  return `${now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

/**
 * INTERNAL: Validates token format.
 */
function isValidToken(token) {
  return typeof token === 'string' && /^[\w-]{16,}$/.test(token);
}

/**
 * INTERNAL: Broadcast token to other tabs (multi-tab sync).
 */
function broadcastToken(token) {
  if (csrfChannel) {
    csrfChannel.postMessage({ type: 'rotate', token });
  }
}

/**
 * INTERNAL: Init BroadcastChannel for token sync.
 */
function ensureChannel() {
  if ('BroadcastChannel' in window && !csrfChannel) {
    csrfChannel = new BroadcastChannel(CSRF_CHANNEL);
    csrfChannel.onmessage = (e) => {
      if (e.data?.type === 'rotate' && isValidToken(e.data.token)) {
        storeToken(e.data.token);
      }
    };
  }
}
