// CSRF Token Utilities (Next-Gen Hardened v8.4)
// Author: Thronestead Security Suite
// Version: 8.4.2025.07.18

const CSRF_TOKEN_KEY = 'csrf_token';
const CSRF_META_KEY = 'csrf_token_ts';
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_CHANNEL = 'csrf-sync';
const DEFAULT_EXPIRY_MS = 6 * 60 * 60 * 1000; // 6 hours

let csrfChannel = null;
let now = () => Date.now();
let expiryMs = DEFAULT_EXPIRY_MS;
let fallbackToken = null;
let tokenLock = false;
let broadcastWait = false;
let storeLock = false;

let storage = {
  get: (key) => sessionStorage.getItem(key),
  set: (key, value) => sessionStorage.setItem(key, value),
  remove: (key) => sessionStorage.removeItem(key),
};

export async function initCsrf(options = {}) {
  ensureChannel();
  if (options.expiryMs && Number.isInteger(options.expiryMs)) expiryMs = options.expiryMs;
  if (broadcastWait || tokenLock) await new Promise(res => setTimeout(res, 250));

  const stored = getStoredToken();
  return stored && !isExpired(stored.timestamp)
    ? stored.token
    : await rotateCsrfToken();
}

export async function rotateCsrfToken() {
  try {
    const token = generateToken();
    storeToken(token, 'rotate');
    broadcastToken(token);
    return token;
  } catch (err) {
    console.error('[CSRF] Token rotation failed:', err);
    return null;
  }
}

export function getCsrfToken() {
  const stored = getStoredToken();
  return stored && !isExpired(stored.timestamp) ? stored.token : null;
}

export function getCsrfMeta() {
  const stored = getStoredToken();
  return stored
    ? { token: stored.token, expiresInMs: expiryMs - (now() - stored.timestamp) }
    : null;
}

export function clearCsrfToken() {
  try {
    storage.remove(CSRF_TOKEN_KEY);
    storage.remove(CSRF_META_KEY);
    localStorage.removeItem(CSRF_TOKEN_KEY);
    localStorage.removeItem(CSRF_META_KEY);
    document.cookie = `${CSRF_COOKIE_NAME}=; Path=/; Max-Age=0; Secure; SameSite=Strict`;
  } catch {}
  fallbackToken = null;
}

export function injectNow(fn) {
  if (typeof fn === 'function') now = fn;
}

export function injectStorage(getFn, setFn, removeFn) {
  if (typeof getFn === 'function') storage.get = getFn;
  if (typeof setFn === 'function') storage.set = setFn;
  if (typeof removeFn === 'function') storage.remove = removeFn;
}

// Internal
function getStoredToken() {
  try {
    const token = storage.get(CSRF_TOKEN_KEY);
    const ts = Number(storage.get(CSRF_META_KEY));
    if (!isValidToken(token)) throw new Error();
    return { token, timestamp: isNaN(ts) ? 0 : ts, source: 'sessionStorage' };
  } catch {
    try {
      const token = localStorage.getItem(CSRF_TOKEN_KEY);
      const ts = Number(localStorage.getItem(CSRF_META_KEY));
      if (isValidToken(token) && !isExpired(ts)) {
        return { token, timestamp: ts, source: 'localStorage' };
      }
    } catch {}

    const cookieToken = readCookie(CSRF_COOKIE_NAME);
    if (isValidToken(cookieToken)) {
      const ts = now() - (expiryMs / 2);
      fallbackToken = { token: cookieToken, timestamp: ts, source: 'cookie' };
      return fallbackToken;
    }

    if (fallbackToken && !isExpired(fallbackToken.timestamp)) {
      return fallbackToken;
    }

    return null;
  }
}

function storeToken(token, source = 'store') {
  if (storeLock) return;
  storeLock = true;

  const jitter = Math.floor(Math.random() * 20000) - 10000; // ±10s
  const timestamp = now();
  const expiresAt = timestamp + expiryMs + jitter;

  try {
    storage.set(CSRF_TOKEN_KEY, token);
    storage.set(CSRF_META_KEY, timestamp.toString());
  } catch {
    fallbackToken = { token, timestamp, source: 'fallback-session-fail' };
  }

  try {
    setCookie(CSRF_COOKIE_NAME, token, expiresAt);
    localStorage.setItem(CSRF_TOKEN_KEY, token);
    localStorage.setItem(CSRF_META_KEY, timestamp.toString());
  } catch (err) {
    console.warn('[CSRF] Persist failure:', err);
    fallbackToken = { token, timestamp, source: 'fallback-local-fail' };
  }

  if (import.meta?.env?.DEV) {
    console.debug(`[CSRF] Token stored (${source}). TTL (ms): ${expiryMs - (now() - timestamp)} — token=${token}`);
  }

  setTimeout(() => { storeLock = false; }, 50);
}

function isExpired(ts) {
  return now() - ts > expiryMs;
}

function setCookie(name, value, expiresAt) {
  if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
    console.warn('[CSRF] Insecure origin — Secure cookies may not apply.');
  }
  const maxAge = Math.floor((expiresAt - now()) / 1000);
  try {
    document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; Max-Age=${maxAge}; Path=/; Secure; SameSite=Strict`;
  } catch (err) {
    console.error('[CSRF] Cookie write error:', err);
  }
}

function readCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + encodeURIComponent(name) + '=([^;]+)');
  return match ? decodeURIComponent(match[2]) : null;
}

function generateToken() {
  if (crypto?.randomUUID) return crypto.randomUUID();
  if (crypto?.getRandomValues) {
    const arr = new Uint8Array(16);
    crypto.getRandomValues(arr);
    return [...arr].map(b => b.toString(16).padStart(2, '0')).join('');
  }
  return `tkn-${now().toString(36)}-${Math.random().toString(36).slice(2, 18)}`.padEnd(32, 'x');
}

function isValidToken(token) {
  return typeof token === 'string' && /^[\w-]{16,}$/.test(token) && token.length >= 32;
}

function broadcastToken(token) {
  if (typeof token !== 'string') return;
  if (csrfChannel) {
    const current = getCsrfToken();
    if (current === token) return; // Avoid rebroadcast
    tokenLock = true;
    csrfChannel.postMessage({ type: 'rotate', token });
    setTimeout(() => { tokenLock = false; }, 250);
  }
}

function ensureChannel() {
  if (csrfChannel || typeof window === 'undefined') return;

  if ('BroadcastChannel' in window) {
    csrfChannel = new BroadcastChannel(CSRF_CHANNEL);
    csrfChannel.onmessage = (e) => {
      const incoming = e.data?.token;
      if (e.data?.type === 'rotate' && isValidToken(incoming)) {
        const current = getCsrfToken();
        if (!current || current !== incoming) storeToken(incoming, 'broadcast');
      }
    };
    broadcastWait = true;
    setTimeout(() => { broadcastWait = false; }, 250);
    if (import.meta?.env?.DEV) {
      console.debug('[CSRF] BroadcastChannel ready');
    }
  }

  if (window?.addEventListener) {
    window.addEventListener('storage', (e) => {
      if (e.key === CSRF_TOKEN_KEY && isValidToken(e.newValue)) {
        const current = getCsrfToken();
        if (!current || current !== e.newValue) storeToken(e.newValue, 'storage');
      }
    });
  }
}
