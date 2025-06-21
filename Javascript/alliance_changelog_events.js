// Project Name: Thronestead©
// File Name: alliance_changelog_events.js
// Version 6.17.2025.00.00
// Developer: Codex
import { applyFilters, fetchChangelog } from './alliance_changelog.js';

document.getElementById('apply-filters-btn')?.addEventListener('click', applyFilters);

document.getElementById('refresh-btn')?.addEventListener('click', fetchChangelog);
