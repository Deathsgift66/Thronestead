// Project Name: Kingmakers Rise©
// File Name: alliance_changelog.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

let changelogData = [];
let latestTimestamp = null;

/**
 * Fetch alliance changelog entries from the backend.
 * If `latestTimestamp` is set, only fetch entries since that point.
 */
async function fetchChangelog() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      window.location.href = 'login.html';
      return;
    }

    const url = latestTimestamp
      ? `/api/alliance/changelog?since=${encodeURIComponent(latestTimestamp)}`
      : '/api/alliance/changelog';

    const res = await fetch(url, {
      headers: { 'X-User-ID': session.user.id }
    });
    if (!res.ok) throw new Error('Failed to fetch changelog');
    const newData = await res.json();

    if (latestTimestamp) {
      const marked = newData.map(e => ({ ...e, new: true }));
      changelogData = [...marked, ...changelogData];
    } else {
      changelogData = newData;
    }

    if (changelogData.length) {
      latestTimestamp = changelogData[0].timestamp;
    }

    const lastEl = document.getElementById('last-updated');
    if (lastEl && latestTimestamp) {
      lastEl.textContent = new Date(latestTimestamp).toLocaleString();
    }

    renderChangelog(changelogData);
  } catch (err) {
    console.error('❌ Error fetching changelog:', err);
  }
}

/**
 * Apply filter UI inputs to changelog data.
 */
function applyFilters() {
  const startVal = document.getElementById('filter-start')?.value;
  const endVal = document.getElementById('filter-end')?.value;
  const typeVal = document.getElementById('filter-type')?.value;

  let filtered = [...changelogData];

  if (startVal) {
    const startDate = new Date(startVal);
    filtered = filtered.filter(entry => new Date(entry.timestamp) >= startDate);
  }

  if (endVal) {
    const endDate = new Date(endVal);
    endDate.setDate(endDate.getDate() + 1); // include entire end day
    filtered = filtered.filter(entry => new Date(entry.timestamp) < endDate);
  }

  if (typeVal) {
    filtered = filtered.filter(entry => entry.event_type === typeVal);
  }

  renderChangelog(filtered);
}

/**
 * Render changelog entries to the list container.
 * New entries (just fetched) are marked with a highlight.
 */
function renderChangelog(list) {
  const container = document.getElementById('changelog-list');
  if (!container) return;

  container.innerHTML = '';

  list.forEach(entry => {
    const li = document.createElement('li');
    li.classList.add('log-entry');
    if (entry.new) li.classList.add('new-entry');

    li.innerHTML = `
      <div class="log-time">${new Date(entry.timestamp).toLocaleString()}</div>
      <div class="log-type ${escapeHTML(entry.event_type)}">${escapeHTML(entry.event_type)}</div>
      <div class="log-description">${escapeHTML(entry.description)}</div>
    `;

    container.appendChild(li);
  });

  // Clear new flag after render
  list.forEach(e => delete e.new);
}

// Basic HTML escaping to prevent XSS injection
function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ✅ Initialize changelog on DOM load
document.addEventListener('DOMContentLoaded', () => {
  fetchChangelog();
  setInterval(fetchChangelog, 30000); // refresh every 30s
});
