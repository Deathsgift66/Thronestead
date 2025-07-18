// CSRF Token Utilities (Next-Gen Hardened v6)
// Author: Thronestead Security Suite
// Version: 6.0.2025.07.18

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_META_KEY = 'csrf_token_ts';
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_CHANNEL = 'csrf-sync';
const DEFAULT_EXPIRY_MS = 6 * 60 * 60 * 1000; // 6 hours

let csrfChannel = null;
let now = () => Date.now(); // injectable for testing
let expiryMs = DEFAULT_EXPIRY_MS;
let fallbackToken = null;
let broadcastWait = false;

/**
 * Initializes and returns a valid CSRF token.
 */
export async function initCsrf(options = {}) {
  ensureChannel();
  if (options.expiryMs && Number.isInteger(options.expiryMs)) expiryMs = options.expiryMs;

  if (broadcastWait) await new Promise(res => setTimeout(res, 250));

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
 * Injects a custom time provider (for tests).
 */
export function injectNow(fn) {
  if (typeof fn === 'function') now = fn;
}

/* ===== Internal Utilities ===== */

function getStoredToken() {
  try {
    const token = sessionStorage.getItem(CSRF_TOKEN_KEY);
    const ts = Number(sessionStorage.getItem(CSRF_META_KEY));
    if (!isValidToken(token)) throw new Error('Invalid or missing token');
    return { token, timestamp: isNaN(ts) ? 0 : ts };
  } catch {
    return fallbackToken;
  }
}

function storeToken(token) {
  const timestamp = now();
  try {
    sessionStorage.setItem(CSRF_TOKEN_KEY, token);
    sessionStorage.setItem(CSRF_META_KEY, timestamp.toString());
  } catch {
    fallbackToken = { token, timestamp };
  }

  try {
    const safeExpiry = timestamp + expiryMs;
    setCookie(CSRF_COOKIE_NAME, token, safeExpiry);
    localStorage.setItem(CSRF_TOKEN_KEY, token); // fallback sync
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
  if (csrfChannel || typeof window === 'undefined') return;

  if ('BroadcastChannel' in window) {
    csrfChannel = new BroadcastChannel(CSRF_CHANNEL);
    csrfChannel.onmessage = (e) => {
      if (e.data?.type === 'rotate' && isValidToken(e.data.token)) {
        const current = getCsrfToken();
        if (!current || current !== e.data.token) {
          storeToken(e.data.token);
        }
      }
    };
    broadcastWait = true;
    setTimeout(() => { broadcastWait = false; }, 250);
    console.info('[CSRF] BroadcastChannel initialized');
  }

  // Fallback for Safari / no BroadcastChannel
  window.addEventListener('storage', (e) => {
    if (e.key === CSRF_TOKEN_KEY && isValidToken(e.newValue)) {
      const current = getCsrfToken();
      if (!current || current !== e.newValue) {
        storeToken(e.newValue);
      }
    }
  });
}
