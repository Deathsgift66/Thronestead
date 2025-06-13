import { supabase } from './supabaseClient.js';

let changelogData = [];
let latestTimestamp = null;

async function fetchChangelog() {
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
}

function applyFilters() {
  const start = document.getElementById('filter-start').value;
  const end = document.getElementById('filter-end').value;
  const type = document.getElementById('filter-type').value;

  let filtered = [...changelogData];
  if (start) {
    const s = new Date(start);
    filtered = filtered.filter(e => new Date(e.timestamp) >= s);
  }
  if (end) {
    const e = new Date(end);
    // add one day to include end date fully
    e.setDate(e.getDate() + 1);
    filtered = filtered.filter(ei => new Date(ei.timestamp) < e);
  }
  if (type) {
    filtered = filtered.filter(e => e.event_type === type);
  }

  renderChangelog(filtered);
}

function renderChangelog(list) {
  const container = document.getElementById('changelog-list');
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
  list.forEach(e => { delete e.new; });
}

window.addEventListener('DOMContentLoaded', fetchChangelog);
window.addEventListener('DOMContentLoaded', () => {
  setInterval(fetchChangelog, 30000);
});

// Basic HTML escape helper
function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
