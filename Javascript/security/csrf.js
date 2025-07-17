// CSRF token helper functions
// Extracted for reuse across admin pages
export function initCsrf() {
  let token = sessionStorage.getItem('csrf_token');
  if (!token) {
    token = crypto.randomUUID();
    sessionStorage.setItem('csrf_token', token);
  }
  setCookie(token);
  return token;
}

export function rotateCsrfToken() {
  const token = crypto.randomUUID();
  sessionStorage.setItem('csrf_token', token);
  setCookie(token);
  return token;
}

function setCookie(token) {
  document.cookie = `csrf_token=${token}; path=/; Secure; SameSite=Strict`;
}

export function getCsrfToken() {
  return sessionStorage.getItem('csrf_token');
}
