// Project Name: Thronestead©
// File Name: utils.js
// Version 6.18.2025.22.00
// Developer: Codex
// Shared frontend utilities for DOM helpers and validation.
import { authHeaders, refreshSessionAndStore, clearStoredAuth } from './auth.js';

/**
 * Escape HTML special characters to prevent injection.
 * @param {string} str Potentially unsafe text
 * @returns {string} Sanitized text
 */
export function escapeHTML(str = '') {
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
export function showToast(msg) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast-notification';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
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
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString();
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
  const opts = {
    headers: { Accept: 'application/json', ...(options.headers || {}) },
    ...options
  };

  const res = await fetch(url, opts);
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
 * Perform a fetch request with Supabase auth headers automatically applied.
 * @param {string} url Request URL
 * @param {object} [options] Fetch options
 * @returns {Promise<Response>} Fetch response
 */
export async function authFetch(url, options = {}) {
  let headers = {
    ...(options.headers || {}),
    ...(await authHeaders())
  };
  let res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    const refreshed = await refreshSessionAndStore();
    if (refreshed) {
      headers = { ...(options.headers || {}), ...(await authHeaders()) };
      res = await fetch(url, { ...options, headers });
    }
    if (res.status === 401) {
      clearStoredAuth();
      window.location.href = 'login.html';
      throw new Error('Unauthorized');
    }
  }

  return res;
}

/**
 * Convenience wrapper around {@link jsonFetch} that also includes auth headers.
 * @param {string} url Request URL
 * @param {object} [options] Fetch options
 * @returns {Promise<any>} Parsed JSON data
 */
export async function authJsonFetch(url, options = {}) {
  const res = await authFetch(url, options);
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


