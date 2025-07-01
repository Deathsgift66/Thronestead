// Project Name: Thronestead©
// File Name: alliance_changelog_events.js
// Version 7.01.2025.08.00
// Developer: Codex (KISS Optimized)

import { applyFilters, fetchChangelog } from './alliance_changelog.js';

function bindEvent(id, handler) {
  document.getElementById(id)?.addEventListener('click', handler);
}

document.addEventListener('DOMContentLoaded', () => {
  bindEvent('apply-filters-btn', applyFilters);
  bindEvent('refresh-btn', fetchChangelog);
});
