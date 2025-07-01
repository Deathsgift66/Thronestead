// Project Name: Thronestead©
// File Name: alliance_changelog.js
// Version 7.01.2025.08.00
// Developer: Codex (KISS Optimized)

import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';
import { authFetchJson } from './fetchJson.js';

let changelogData = [];

// 📥 Fetch & render changelog
export async function fetchChangelog() {
  try {
    const { data: { session } = {} } = await supabase.auth.getSession();
    if (!session) return (window.location.href = 'login.html');

    const filters = ['start', 'end', 'type'].reduce((params, key) => {
      const val = document.getElementById(`filter-${key}`)?.value;
      if (val) params.set(key, val);
      return params;
    }, new URLSearchParams());

    const data = await authFetchJson(`/api/alliance/changelog?${filters}`, session);
    changelogData = data.logs || [];

    updateLastUpdated(data.last_updated);
    renderChangelog(changelogData);
  } catch (err) {
    console.error('❌ Error fetching changelog:', err);
  }
}

// 🔄 Re-fetch with filters
export function applyFilters() {
  fetchChangelog();
}

// 📅 Update timestamp
function updateLastUpdated(timestamp) {
  const el = document.getElementById('last-updated');
  if (el && timestamp) el.textContent = new Date(timestamp).toLocaleString();
}

// 📝 Render logs to DOM
function renderChangelog(logs) {
  const container = document.getElementById('changelog-list');
  if (!container) return;

  if (!logs.length) {
    container.innerHTML = '<li class="empty-state">No historical records match your filters.</li>';
    return;
  }

  container.innerHTML = logs.map(log => `
    <li class="timeline-entry ${escapeHTML(log.event_type)}" role="article" aria-label="Changelog entry">
      <div class="timeline-bullet"></div>
      <div class="timeline-content">
        <span class="log-type">${escapeHTML(log.event_type.toUpperCase())}</span>
        <p class="log-text">${escapeHTML(log.description)}</p>
        <time datetime="${log.timestamp}">${new Date(log.timestamp).toLocaleString()}</time>
      </div>
    </li>
  `).join('');
}

// 🚀 Init changelog on page load
document.addEventListener('DOMContentLoaded', () => {
  fetchChangelog();
  setInterval(fetchChangelog, 30000); // auto-refresh every 30s
});
