// Project Name: Thronestead©
// File Name: alliance_changelog.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';
import { authFetchJson } from './fetchJson.js';

let changelogData = [];

/**
 * Fetch alliance changelog entries from the backend
 * using filter inputs if provided.
 */
export async function fetchChangelog() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      window.location.href = 'login.html';
      return;
    }

    const params = new URLSearchParams();
    const startVal = document.getElementById('filter-start')?.value;
    const endVal = document.getElementById('filter-end')?.value;
    const typeVal = document.getElementById('filter-type')?.value;
    if (startVal) params.set('start', startVal);
    if (endVal) params.set('end', endVal);
    if (typeVal) params.set('type', typeVal);

    const data = await authFetchJson(`https://thronestead.onrender.com/api/alliance/changelog?${params}`, session);

    changelogData = data.logs || [];

    const lastEl = document.getElementById('last-updated');
    if (lastEl && data.last_updated) {
      lastEl.textContent = new Date(data.last_updated).toLocaleString();
    }

    const listEl = document.getElementById('changelog-list');
    if (changelogData.length === 0) {
      listEl.innerHTML = '<li class="empty-state">No historical records match your filters.</li>';
      return;
    }

    renderChangelog(changelogData);
  } catch (err) {
    console.error('❌ Error fetching changelog:', err);
  }
}

/**
 * Apply filter UI inputs to changelog data.
 */
export function applyFilters() {
  fetchChangelog();
}

/**
 * Render changelog entries to the list container.
 * New entries (just fetched) are marked with a highlight.
 */
function renderChangelog(list) {
  const container = document.getElementById('changelog-list');
  if (!container) return;

  container.innerHTML = '';

  list.forEach(log => {
    const li = document.createElement('li');
    li.classList.add('timeline-entry', log.event_type);
    li.setAttribute('role', 'article');
    li.setAttribute('aria-label', 'Changelog entry');
    li.innerHTML = `
      <div class="timeline-bullet"></div>
      <div class="timeline-content">
        <span class="log-type">${escapeHTML(log.event_type.toUpperCase())}</span>
        <p class="log-text">${escapeHTML(log.description)}</p>
        <time datetime="${log.timestamp}">${new Date(log.timestamp).toLocaleString()}</time>
      </div>
    `;

    container.appendChild(li);
  });
}

// ✅ Initialize changelog on DOM load
document.addEventListener('DOMContentLoaded', () => {
  fetchChangelog();
  setInterval(fetchChangelog, 30000); // refresh every 30s
});
