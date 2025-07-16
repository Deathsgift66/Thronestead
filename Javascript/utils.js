// Project Name: Thronestead©
// File Name: utils.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Shared frontend utilities for DOM helpers and validation.
import { authHeaders, refreshSessionAndStore, clearStoredAuth } from './auth.js';
import { getReauthHeaders } from './reauth.js';
import { supabase } from '../supabaseClient.js';

export const safeUUID = () =>
  crypto?.randomUUID?.() ||
  ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
    (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> (c / 4)).toString(16)
  );

/**
 * Escape HTML special characters to prevent injection.
 * @param {string} str Potentially unsafe text
 * @returns {string} Sanitized text
 */
export function escapeHTML(str = '') {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Display a temporary toast notification.
 * Creates the container dynamically if it does not exist.
 * @param {string} msg Message to display
 */
export function showToast(msg, type = 'info') {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast-notification';
    toast.setAttribute('tabindex', '-1');
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.setAttribute('aria-hidden', 'true');
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.className = `toast-notification ${type}`;
  toast.setAttribute('aria-hidden', 'false');
  toast.classList.add('show');
  toast.focus();
  setTimeout(() => {
    toast.classList.remove('show');
    toast.setAttribute('aria-hidden', 'true');
  }, 3000);
}

/**
 * Toggle the global loading spinner visibility.
 * @param {boolean} show When true show the spinner, otherwise hide it
 */
export function toggleLoading(show) {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.toggle('visible', show);
}

/**
 * Display a modal element by id or reference.
 * Removes the "hidden" class and updates ARIA attributes.
 * @param {string|HTMLElement} modal Target modal or id
 */
export function openModal(modal) {
  const el = typeof modal === 'string' ? document.getElementById(modal) : modal;
  if (!el) return;
  el.__prevFocus = document.activeElement;
  el.classList.remove('hidden');
  el.setAttribute('aria-hidden', 'false');
  el.removeAttribute('inert');

  const focusable = el.querySelectorAll(
    'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  const trap = e => {
    if (e.key === 'Escape') {
      closeModal(el);
    } else if (e.key === 'Tab' && focusable.length) {
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  };

  const outside = e => {
    if (e.target === el) closeModal(el);
  };

  el.__trapFocus = trap;
  el.__outsideClick = outside;
  el.addEventListener('keydown', trap);
  el.addEventListener('click', outside);
  if (first) first.focus();
}

/**
 * Hide a modal element by id or reference.
 * Adds the "hidden" class and updates ARIA attributes.
 * @param {string|HTMLElement} modal Target modal or id
 */
export function closeModal(modal) {
  const el = typeof modal === 'string' ? document.getElementById(modal) : modal;
  if (!el) return;
  if (el.contains(document.activeElement)) {
    document.activeElement.blur();
  }
  el.removeEventListener('keydown', el.__trapFocus);
  el.removeEventListener('click', el.__outsideClick);
  delete el.__trapFocus;
  delete el.__outsideClick;
  el.classList.add('hidden');
  el.setAttribute('aria-hidden', 'true');
  el.setAttribute('inert', '');
  if (el.__prevFocus && typeof el.__prevFocus.focus === 'function') {
    el.__prevFocus.focus();
  }
  delete el.__prevFocus;
}

/**
 * Simple email format validation.
 * @param {string} email Email address
 * @returns {boolean} True if valid
 */
export function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate password complexity.
 * Requires lowercase, uppercase, digit, and symbol.
 *
 * @param {string} password Password to validate
 * @returns {boolean} True if password is complex
 */
export function validatePasswordComplexity(password) {
  const pattern = /^(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
  return pattern.test(password);
}

/**
 * Determine if a string is a valid URL.
 * @param {string} str Input string
 * @returns {boolean} True if valid URL
 */
export function isValidURL(str) {
  try {
    new URL(str);
    return true;
  } catch {
    return false;
  }
}

/**
 * Set an element's value by id.
 * @param {string} id Element id
 * @param {string} value New value
 */
export function setValue(id, value) {
  const el = document.getElementById(id);
  if (el) el.value = value;
}

/**
 * Get a trimmed value from an input.
 * @param {string} id Element id
 * @param {boolean} allowNull Return null if empty when true
 * @returns {string|null}
 */
export function getValue(id, allowNull = false) {
  const val = (document.getElementById(id)?.value || '').trim();
  return allowNull && val === '' ? null : val;
}

/**
 * Update the src attribute of an image element.
 * @param {string} id Element id
 * @param {string} value Image URL
 */
export function setSrc(id, value) {
  const el = document.getElementById(id);
  if (el) el.src = value;
}

/**
 * Update the text content of an element.
 * @param {string} id Element id
 * @param {string} value Text to set
 */
export function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

/**
 * Format a timestamp using the user's locale.
 * @param {string|number|Date} ts Date or timestamp
 * @returns {string} Locale formatted string
 */
export function formatDate(ts) {
  const date = ts instanceof Date ? ts : new Date(ts);
  return Number.isNaN(date.getTime())
    ? ''
    : date.toLocaleString('en-US', { timeZone: 'UTC' });
}

/**
 * Format a timestamp relative to now, e.g. "2 days ago".
 * @param {string|number|Date} ts Date or timestamp
 * @returns {string} Relative time string
 */
export function relativeTime(ts) {
  const date = ts instanceof Date ? ts : new Date(ts);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (Number.isNaN(seconds)) return '';
  const units = [
    { sec: 31536000, label: 'year' },
    { sec: 2592000, label: 'month' },
    { sec: 604800, label: 'week' },
    { sec: 86400, label: 'day' },
    { sec: 3600, label: 'hour' },
    { sec: 60, label: 'minute' }
  ];
  for (const { sec, label } of units) {
    const count = Math.floor(seconds / sec);
    if (count >= 1) return `${count} ${label}${count > 1 ? 's' : ''} ago`;
  }
  return 'just now';
}

/**
 * Fetch JSON from an endpoint with sensible defaults and error handling.
 *
 * This helper ensures the "Accept" header is set and rejects on
 * non-2xx responses or invalid JSON payloads.
 *
 * @param {string} url       Request URL
 * @param {object} [options] fetch options
 * @returns {Promise<any>}   Parsed JSON data
 */
export async function jsonFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: { Accept: 'application/json', ...(options.headers || {}) },
    credentials: options.credentials || 'include',
    ...options
  });
  return parseJsonResponse(res);
}

/**
 * Perform a fetch request with Supabase auth headers automatically applied.
 * @param {string} url Request URL
 * @param {object} [options] Fetch options
 * @returns {Promise<Response>} Fetch response
 */
export async function authFetch(url, options = {}) {
  let headers = {
    ...(options.headers || {}),
    ...(await authHeaders()),
    ...getReauthHeaders()
  };
  let res = await fetch(url, {
    credentials: options.credentials || 'include',
    ...options,
    headers
  });

  if (res.status === 401) {
    const refreshed = await refreshSessionAndStore();
    if (refreshed) {
      headers = { ...(options.headers || {}), ...(await authHeaders()), ...getReauthHeaders() };
      res = await fetch(url, {
        credentials: options.credentials || 'include',
        ...options,
        headers
      });
    }
    if (res.status === 401) {
      clearStoredAuth();
      window.location.href = 'login.html';
      throw new Error('Unauthorized');
    }
  }

  return res;
}

async function parseJsonResponse(res) {
  const type = res.headers.get('content-type') || '';
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed ${res.status}: ${text}`);
  }
  if (!type.includes('application/json')) {
    throw new Error('Invalid JSON response');
  }
  return res.json();
}

/**
 * Convenience wrapper around {@link jsonFetch} that also includes auth headers.
 * @param {string} url Request URL
 * @param {object} [options] Fetch options
 * @returns {Promise<any>} Parsed JSON data
 */
export async function authJsonFetch(url, options = {}) {
  const res = await authFetch(url, options);
  return parseJsonResponse(res);
}

/**
 * Build a DocumentFragment from an array of items.
 * @template T
 * @param {T[]} items Data items
 * @param {(item:T)=>HTMLElement} builder Function to create an element
 * @returns {DocumentFragment} Fragment with all built elements
 */
export function fragmentFrom(items, builder) {
  const frag = document.createDocumentFragment();
  for (const item of items) {
    const el = builder(item);
    if (el) frag.appendChild(el);
  }
  return frag;
}

/**
 * Remove dangerous elements from an HTML string.
 * This is a lightweight sanitizer for user-generated content.
 *
 * @param {string} html Raw HTML
 * @returns {string} Clean HTML safe for insertion into the DOM
 */
export function sanitizeHTML(html = '') {
  const template = document.createElement('template');
  template.innerHTML = html;
  template.content.querySelectorAll('script, iframe').forEach(el => el.remove());
  return template.innerHTML;
}

/**
 * Create a debounced version of a function.
 * Subsequent calls reset the timer so `fn` executes only
 * after `delay` milliseconds have elapsed without a new call.
 *
 * @param {Function} fn    Callback to debounce
 * @param {number} delay   Delay in milliseconds
 * @returns {Function}     Debounced wrapper
 */
export function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Apply width styles for elements with a `data-width` attribute.
 * Constrains the value between 0 and 100 percent.
 *
 * @param {ParentNode} root DOM scope to search
 */
export function setBarWidths(root = document) {
  root.querySelectorAll('[data-width]').forEach(el => {
    const pct = parseFloat(el.dataset.width);
    if (!Number.isNaN(pct)) {
      el.style.width = `${Math.min(100, Math.max(0, pct))}%`;
    }
  });
}

/**
 * Ensure the current user belongs to an alliance or is an admin.
 * Redirects when unauthorized.
 * @returns {Promise<boolean>} True if authorized
 */
export async function enforceAllianceOrAdminAccess() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      window.location.href = 'login.html';
      return false;
    }

    const [admin, alliance] = await Promise.all([
      supabase.from('users').select('is_admin').eq('user_id', user.id).single(),
      supabase.from('alliance_members').select('user_id').eq('user_id', user.id).maybeSingle()
    ]);

    if (admin.error) console.error(admin.error.message || admin.error);
    if (alliance.error) console.error(alliance.error.message || alliance.error);

    if (admin.data?.is_admin || alliance.data) return true;

    showToast('You must be in an alliance or be an admin to access this page.', 'error');
    window.location.href = 'overview.html';
    return false;
  } catch (err) {
    console.error('❌ Access check error:', err);
    window.location.href = 'overview.html';
    return false;
  }
}


