import { supabase } from './supabaseClient.js';

let changelogData = [];

async function fetchChangelog() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  const res = await fetch('/api/alliance/changelog', {
    headers: { 'X-User-ID': session.user.id }
  });
  changelogData = await res.json();
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
    li.innerHTML = `
      <div class="log-time">${new Date(entry.timestamp).toLocaleString()}</div>
      <div class="log-type">${entry.event_type}</div>
      <div class="log-description">${entry.description}</div>
    `;
    container.appendChild(li);
  });
}

window.addEventListener('DOMContentLoaded', fetchChangelog);
