// Project Name: Thronestead©
// File Name: utils_admin.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Utility helpers for admin-only pages

import {
  authFetch,
  authJsonFetch,
  escapeHTML,
  showToast,
  openModal,
  closeModal,
  toggleLoading,
  debounce,
  getCsrfToken
} from './utils.js';

export {
  authFetch,
  authJsonFetch,
  escapeHTML,
  showToast,
  openModal,
  closeModal,
  toggleLoading,
  debounce
};

export function getNumberInputValue(id) {
  const val = document.getElementById(id)?.value.trim();
  if (!val) return null;
  const num = Number(val);
  return Number.isInteger(num) && num > 0 ? num : null;
}

export async function postAction(url, payload) {
  const res = await authFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() },
    referrerPolicy: 'strict-origin',
    body: JSON.stringify(payload)
  });
  const type = res.headers.get('content-type') || '';
  let data;
  if (type.includes('application/json')) {
    try {
      data = await res.json();
    } catch {
      throw new Error('Invalid JSON response');
    }
  } else {
    data = await res.text();
  }
  if (!res.ok) {
    const detail = typeof data === 'string' ? data : data.detail || JSON.stringify(data);
    throw new Error(detail);
  }
  return data;
}

export function applyFilter(listEl, term) {
  const items = Array.from(listEl.children);
  items.forEach(li => {
    const q = li.dataset.queue?.toLowerCase() || '';
    li.style.display = q.includes(term) ? '' : 'none';
  });
}
