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
 * Requires an element with id="toast" in the DOM.
 * @param {string} msg Message to display
 */
export function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
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

