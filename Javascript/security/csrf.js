// CSRF Token Utilities (Next-Gen Hardened v7.1)
// Author: Thronestead Security Suite
// Version: 7.1.2025.07.18

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_META_KEY = 'csrf_token_ts';
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_CHANNEL = 'csrf-sync';
const DEFAULT_EXPIRY_MS = 6 * 60 * 60 * 1000; // 6 hours

let csrfChannel = null;
let now = () => Date.now();
let expiryMs = DEFAULT_EXPIRY_MS;
let fallbackToken = null;
let broadcastWait = false;
let tokenLock = false;

// Injectable storage functions for testing
let storage = {
  get: (key) => sessionStorage.getItem(key),
  set: (key, value) => sessionStorage.setItem(key, value),
  remove: (key) => sessionStorage.removeItem(key)
};

/**
 * Initializes and returns a valid CSRF token.
 */
export async function initCsrf(options = {}) {
  ensureChannel();
  if (options.expiryMs && Number.isInteger(options.expiryMs)) expiryMs = options.expiryMs;

  if (broadcastWait || tokenLock) await new Promise(res => setTimeout(res, 250));

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
 * Returns current CSRF token or null if invalid/expired.
 */
export function getCsrfToken() {
  const stored = getStoredToken();
  return stored && !isExpired(stored.timestamp) ? stored.token : null;
}

/**
 * Returns token + expiry info (for debugging).
 */
export function getCsrfMeta() {
  const stored = getStoredToken();
  return stored
    ? { token: stored.token, expiresInMs: expiryMs - (now() - stored.timestamp) }
    : null;
}

/**
 * Clears all CSRF tokens manually (e.g. on logout).
 */
export function clearCsrfToken() {
  try {
    storage.remove(CSRF_TOKEN_KEY);
    storage.remove(CSRF_META_KEY);
    localStorage.removeItem(CSRF_TOKEN_KEY);
    localStorage.removeItem(CSRF_META_KEY);
    document.cookie = `${CSRF_COOKIE_NAME}=; Path=/; Max-Age=0; Secure; SameSite=Strict`;
    if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
      console.warn('[CSRF] Token clear may not affect Secure cookie on non-HTTPS origin.');
    }
  } catch {}
  fallbackToken = null;
}

/**
 * Injects a custom time provider (for testing).
 */
export function injectNow(fn) {
  if (typeof fn === 'function') now = fn;
}

/**
 * Injects custom storage for testing.
 */
export function injectStorage(getFn, setFn, removeFn) {
  if (typeof getFn === 'function') storage.get = getFn;
  if (typeof setFn === 'function') storage.set = setFn;
  if (typeof removeFn === 'function') storage.remove = removeFn;
}

/* ===== Internal Utilities ===== */

function getStoredToken() {
  try {
    const token = storage.get(CSRF_TOKEN_KEY);
    const ts = Number(storage.get(CSRF_META_KEY));
    if (!isValidToken(token)) throw new Error('Invalid or missing token');
    return { token, timestamp: isNaN(ts) ? 0 : ts };
  } catch {
    try {
      const token = localStorage.getItem(CSRF_TOKEN_KEY);
      const ts = Number(localStorage.getItem(CSRF_META_KEY));
      if (isValidToken(token) && !isExpired(ts)) {
        return { token, timestamp: ts };
      }
    } catch {}

    // Fallback to cookie
    const cookieToken = readCookie(CSRF_COOKIE_NAME);
    if (isValidToken(cookieToken)) {
      return { token: cookieToken, timestamp: now() }; // no accurate timestamp
    }

    return fallbackToken && !isExpired(fallbackToken.timestamp) ? fallbackToken : null;
  }
}

function storeToken(token) {
  const timestamp = now();
  const existing = getStoredToken();
  if (existing && existing.token === token && !isExpired(existing.timestamp)) return;

  try {
    storage.set(CSRF_TOKEN_KEY, token);
    storage.set(CSRF_META_KEY, timestamp.toString());
  } catch {
    fallbackToken = { token, timestamp };
  }

  try {
    const safeExpiry = timestamp + expiryMs;
    setCookie(CSRF_COOKIE_NAME, token, safeExpiry);
    localStorage.setItem(CSRF_TOKEN_KEY, token);
    localStorage.setItem(CSRF_META_KEY, timestamp.toString());
  } catch (err) {
    console.warn('[CSRF] Failed to persist token to cookie/localStorage:', err);
  }
}

function isExpired(ts) {
  return now() - ts > expiryMs;
}

function setCookie(name, value, expiresAt) {
  if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
    console.warn('[CSRF] Insecure context — Secure cookies may not be honored.');
  }
  const expires = `; Expires=${new Date(expiresAt).toUTCString()}`;
  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; Path=/; Secure; SameSite=Strict${expires}`;
}

function readCookie(name) {
  return document.cookie.split('; ').reduce((acc, kv) => {
    const [k, v] = kv.split('=');
    return k === name ? decodeURIComponent(v) : acc;
  }, null);
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
  tokenLock = true;
  if (csrfChannel) {
    csrfChannel.postMessage({ type: 'rotate', token });
  }
  setTimeout(() => { tokenLock = false; }, 100);
}

function ensureChannel() {
  if (csrfChannel || typeof window === 'undefined') return;

  if ('BroadcastChannel' in window) {
    csrfChannel = new BroadcastChannel(CSRF_CHANNEL);
    csrfChannel.onmessage = (e) => {
      const incoming = e.data?.token;
      if (e.data?.type === 'rotate' && isValidToken(incoming)) {
        const current = getCsrfToken();
        if ((!current || current !== incoming) && !isExpired(now())) {
          storeToken(incoming);
        }
      }
    };
    broadcastWait = true;
    setTimeout(() => { broadcastWait = false; }, 250);
    console.info('[CSRF] BroadcastChannel initialized');
  }

  window.addEventListener('storage', (e) => {
    if (e.key === CSRF_TOKEN_KEY && isValidToken(e.newValue)) {
      const current = getCsrfToken();
      if (!current || current !== e.newValue) {
        storeToken(e.newValue);
      }
    }
  });
}
