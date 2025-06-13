/*
Project Name: Kingmakers Rise Frontend
File Name: conflicts.js
Updated: July 2025
Description: Dynamic conflict listing with filters and sorting.
*/

import { supabase } from './supabaseClient.js';

let accessToken = null;
let userId = null;

const REFRESH_MS = 30000;
let conflicts = [];
let currentFilter = 'all';
let sortBy = 'started_at';
let sortDir = 'desc';

// Initialize after DOM ready
document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  accessToken = session.access_token;
  userId = session.user.id;
  setupControls();
  await loadConflicts();
  startAutoRefresh();
});

function setupControls() {
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      applyFilters();
    });
  });
  const search = document.getElementById('conflictSearch');
  if (search) search.addEventListener('input', applyFilters);
  document.querySelectorAll('#conflictTable th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const field = th.dataset.field;
      if (sortBy === field) {
        sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        sortBy = field;
        sortDir = 'asc';
      }
      applyFilters();
    });
  });
}

async function loadConflicts() {
  const tbody = document.getElementById('conflictRows');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="10">Loading conflicts...</td></tr>';
  try {
    const res = await fetch('/api/conflicts/overview', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-User-ID': userId
      }
    });
    const data = await res.json();
    conflicts = data.wars || [];
    applyFilters();
  } catch (err) {
    console.error('Error loading conflicts:', err);
    tbody.innerHTML = '<tr><td colspan="10">Failed to load conflicts.</td></tr>';
  }
}

function applyFilters() {
  const searchEl = document.getElementById('conflictSearch');
  const search = searchEl ? searchEl.value.toLowerCase() : '';
  let rows = conflicts.slice();
  if (currentFilter === 'active') rows = rows.filter(r => r.phase === 'live');
  else if (currentFilter === 'concluded') rows = rows.filter(r => r.phase === 'resolved');
  else if (currentFilter === 'planning') rows = rows.filter(r => r.phase === 'planning');
  else if (currentFilter === 'resolution') rows = rows.filter(r => r.phase === 'resolved' && r.winner_side);
  if (search) {
    rows = rows.filter(r =>
      (r.attacker_alliance || '').toLowerCase().includes(search) ||
      (r.defender_alliance || '').toLowerCase().includes(search) ||
      (r.attacker_kingdom || '').toLowerCase().includes(search) ||
      (r.defender_kingdom || '').toLowerCase().includes(search)
    );
  }
  if (sortBy) {
    rows.sort((a, b) => compareFields(a, b, sortBy));
  }
  renderRows(rows);
}

function compareFields(a, b, field) {
  const valA = a[field];
  const valB = b[field];
  if (field === 'started_at') {
    const da = valA ? new Date(valA) : 0;
    const db = valB ? new Date(valB) : 0;
    return sortDir === 'asc' ? da - db : db - da;
  }
  return sortDir === 'asc'
    ? String(valA || '').localeCompare(String(valB || ''))
    : String(valB || '').localeCompare(String(valA || ''));
}

function renderRows(rows) {
  const tbody = document.getElementById('conflictRows');
  if (!tbody) return;
  if (rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10">No conflicts found.</td></tr>';
    return;
  }
  tbody.innerHTML = '';
  rows.forEach(row => {
    const tr = document.createElement('tr');
    const pct = row.battle_tick ? Math.min(row.battle_tick * 100 / 12, 100) : 0;
    const progress = `<div class="progress-bar-bg"><div class="progress-bar-fill" style="width:${pct}%" title="Attacker ${row.attacker_score || 0} / Defender ${row.defender_score || 0}"></div></div>`;
    const statusClass = `status-${row.phase || 'alert'}`;
    tr.innerHTML = `
      <td>${row.war_id}</td>
      <td>${escapeHTML(row.attacker_alliance || row.attacker_kingdom || '')}</td>
      <td>${escapeHTML(row.defender_alliance || row.defender_kingdom || '')}</td>
      <td>${escapeHTML(row.war_type || '')}</td>
      <td>${row.started_at ? new Date(row.started_at).toLocaleDateString() : ''}</td>
      <td class="${statusClass}">${escapeHTML(row.phase || '')}</td>
      <td>${escapeHTML(row.victor || row.winner_side || '')}</td>
      <td>${progress}</td>
      <td>${row.castle_hp ?? ''}</td>
      <td>
        <a href="battle_live.html?war_id=${row.war_id}">View Battle</a>
        ${row.victor || row.winner_side ? ` | <a href="battle_resolution.html?war_id=${row.war_id}">View Resolution</a>` : ''}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function startAutoRefresh() {
  setInterval(loadConflicts, REFRESH_MS);
}

function escapeHTML(str) {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
