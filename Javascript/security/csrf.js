// CSRF Token Utility (v1.1 Production Hardened)
// For secure admin use — extracted and reusable

const CSRF_KEY = 'csrf_token';
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_COOKIE_PATH = '/';

// Initialize CSRF Token if not already set
export function initCsrf() {
  let token = sessionStorage.getItem(CSRF_KEY);
  if (!validateToken(token)) {
    token = rotateCsrfToken(); // sets and returns new one
  } else {
    setCookie(token);
  }
  return token;
}

// Generate a new CSRF token and update storage + cookie
export function rotateCsrfToken() {
  const token = crypto.randomUUID();
  sessionStorage.setItem(CSRF_KEY, token);
  setCookie(token);
  return token;
}

// Set CSRF token as a secure, strict cookie
function setCookie(token) {
  if (!validateToken(token)) return;
  document.cookie = `${CSRF_COOKIE_NAME}=${encodeURIComponent(token)}; path=${CSRF_COOKIE_PATH}; Secure; SameSite=Strict`;
}

// Retrieve current CSRF token from sessionStorage
export function getCsrfToken() {
  const token = sessionStorage.getItem(CSRF_KEY);
  return validateToken(token) ? token : null;
}

// Optional: Validate token format (basic UUID v4 pattern check)
function validateToken(token) {
  return typeof token === 'string' &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(token);
}
