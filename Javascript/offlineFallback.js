// Project Name: Thronestead©
// File Name: offlineFallback.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Utilities for caching kingdom data and enabling fallback mode

/**
 * Store the latest kingdom overview data in localStorage.
 * @param {object} data Overview payload from the API
 */
export function saveKingdomCache(data) {
  try {
    localStorage.setItem('cachedKingdomOverview', JSON.stringify(data));
  } catch (err) {
    console.error('Failed to cache kingdom data:', err);
  }
}

/**
 * Retrieve cached kingdom data from localStorage.
 * @returns {object|null} Cached overview data or null if unavailable
 */
export function loadKingdomCache() {
  try {
    const raw = localStorage.getItem('cachedKingdomOverview');
    return raw ? JSON.parse(raw) : null;
  } catch (err) {
    console.error('Failed to parse kingdom cache:', err);
    return null;
  }
}

/**
 * Activate fallback mode by showing a banner and disabling actions.
 */
export function activateFallbackMode() {
  const banner = document.getElementById('fallback-banner');
  if (banner) banner.hidden = false;
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', e => e.preventDefault());
  });
  document.querySelectorAll('button, input[type="submit"]').forEach(el => {
    el.disabled = true;
  });
}

/**
 * Deactivate fallback mode and re-enable actions.
 */
export function deactivateFallbackMode() {
  const banner = document.getElementById('fallback-banner');
  if (banner) banner.hidden = true;
  document.querySelectorAll('button, input[type="submit"]').forEach(el => {
    el.disabled = false;
  });
}
