// Project Name: Thronestead©
// File Name: alliance_changelog_events.js
// Version 6.17.2025.00.00
// Developer: Codex

document.getElementById('apply-filters-btn')?.addEventListener('click', () => {
  if (typeof applyFilters === 'function') applyFilters();
});

document.getElementById('refresh-btn')?.addEventListener('click', () => {
  if (typeof fetchChangelog === 'function') fetchChangelog();
});
