// Project Name: Kingmakers Rise©
// File Name: utils.js
// Version 6.14.2025.20.12
// Developer: Codex
// Shared frontend utilities for DOM helpers and validation.

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
 * Simple email format validation.
 * @param {string} email Email address
 * @returns {boolean} True if valid
 */
export function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
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


