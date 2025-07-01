// Comment
// Project Name: Thronestead©
// File Name: alliance_changelog_events.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66

import { applyFilters, fetchChangelog } from './alliance_changelog.js';

function bindEvent(id, handler) {
  document.getElementById(id)?.addEventListener('click', handler);
}

document.addEventListener('DOMContentLoaded', () => {
  bindEvent('apply-filters-btn', applyFilters);
  bindEvent('refresh-btn', fetchChangelog);
});
