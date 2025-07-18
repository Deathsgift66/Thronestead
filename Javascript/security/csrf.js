// CSRF Token Utilities (Next-Gen Hardened v5)
// Author: Thronestead Security Suite
// Version: 5.0.2025.07.18

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_META_KEY = 'csrf_token_ts';
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_CHANNEL = 'csrf-sync';
const DEFAULT_EXPIRY_MS = 6 * 60 * 60 * 1000; // 6 hours

let csrfChannel = null;
let now = () => Date.now(); // injectable for testing
let expiryMs = DEFAULT_EXPIRY_MS;

/**
 * Initializes and returns a valid CSRF token.
 */
export function initCsrf(options = {}) {
  ensureChannel();
  if (options.expiryMs && Number.isInteger(options.expiryMs)) expiryMs = options.expiryMs;

  const stored = getStoredToken();
  if (stored && !isExpired(stored.timestamp)) return stored.token;

  return rotateCsrfToken();
}

/**
 * Forces a new CSRF token and syncs it.
 */
export function rotateCsrfToken() {
  const token = generateToken();
  storeToken(token);
  broadcastToken(token);
  return token;
}

/**
 * Returns current CSRF token or null if invalid.
 */
export function getCsrfToken() {
  const stored = getStoredToken();
  return stored && !isExpired(stored.timestamp) ? stored.token : null;
}

/**
 * Injects a custom time provider for test environments.
 */
export function injectNow(fn) {
  if (typeof fn === 'function') now = fn;
}

/* ===== Internal Utilities ===== */

function getStoredToken() {
  try {
    const token = sessionStorage.getItem(CSRF_TOKEN_KEY);
    const ts = Number(sessionStorage.getItem(CSRF_META_KEY));
    if (!isValidToken(token)) return null;
    return { token, timestamp: isNaN(ts) ? 0 : ts };
  } catch (err) {
    console.warn('[CSRF] Failed to read from sessionStorage:', err);
    return null;
  }
}

function storeToken(token) {
  const timestamp = now();
  try {
    sessionStorage.setItem(CSRF_TOKEN_KEY, token);
    sessionStorage.setItem(CSRF_META_KEY, timestamp.toString());
  } catch (err) {
    console.warn('[CSRF] Failed to write to sessionStorage:', err);
  }

  try {
    setCookie(CSRF_COOKIE_NAME, token, timestamp + expiryMs);
  } catch (err) {
    console.warn('[CSRF] Failed to write cookie:', err);
  }
}

function isExpired(ts) {
  return now() - ts > expiryMs;
}

function setCookie(name, value, expiresAt) {
  if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
    console.warn('[CSRF] Insecure context — Secure cookies may be ignored.');
  }
  const expires = expiresAt ? `; Expires=${new Date(expiresAt).toUTCString()}` : '';
  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; Path=/; Secure; SameSite=Strict${expires}`;
}

function generateToken() {
  if (crypto?.randomUUID) return crypto.randomUUID();
  if (crypto?.getRandomValues) {
    const arr = new Uint8Array(16);
    crypto.getRandomValues(arr);
    return [...arr].map(b => b.toString(16).padStart(2, '0')).join('');
  }
  return `tkn-${now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

function isValidToken(token) {
  return typeof token === 'string' && /^[\w-]{16,}$/.test(token);
}

function broadcastToken(token) {
  if (typeof token !== 'string') return;
  if (csrfChannel) {
    csrfChannel.postMessage({ type: 'rotate', token });
  }
}

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
    console.info('[CSRF] BroadcastChannel initialized');
  }
}
