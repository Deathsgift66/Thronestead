// CSRF Token Utilities (Production-Ready)
// Author: Thronestead Security Suite
// Version: 1.0.2025.07.18

const CSRF_TOKEN_KEY = 'csrf_token';

/**
 * Initializes CSRF token if not already present. Returns the token.
 */
export function initCsrf() {
  let token = sessionStorage.getItem(CSRF_TOKEN_KEY);
  if (!isValidToken(token)) {
    token = generateToken();
    storeToken(token);
  }
  return token;
}

/**
 * Rotates the CSRF token forcefully. Returns the new token.
 */
export function rotateCsrfToken() {
  const token = generateToken();
  storeToken(token);
  return token;
}

/**
 * Retrieves the current CSRF token from sessionStorage.
 */
export function getCsrfToken() {
  const token = sessionStorage.getItem(CSRF_TOKEN_KEY);
  return isValidToken(token) ? token : null;
}

/**
 * Sets cookie and sessionStorage with the token.
 */
function storeToken(token) {
  sessionStorage.setItem(CSRF_TOKEN_KEY, token);
  setCookie(CSRF_TOKEN_KEY, token);
}

/**
 * Generates a UUIDv4 token. Add fallback if crypto is unavailable.
 */
function generateToken() {
  return (crypto?.randomUUID?.() || self.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`).toString();
}

/**
 * Validates token format (UUID or fallback pattern).
 */
function isValidToken(token) {
  return typeof token === 'string' && token.length >= 16 && /^[\w-]+$/.test(token);
}

/**
 * Sets a secure, strict-scope cookie.
 */
function setCookie(name, value) {
  document.cookie = `${name}=${value}; Path=/; Secure; SameSite=Strict`;
}
