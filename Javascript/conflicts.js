// Project Name: Kingmakers Rise©
// File Name: conflicts.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

let accessToken = null;
let userId = null;
const REFRESH_MS = 30000;

let conflicts = [];
let currentFilter = 'all';
let sortBy = 'started_at';
let sortDir = 'desc';

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return (window.location.href = 'login.html');
  accessToken = session.access_token;
  userId = session.user.id;

  setupControls();
  await loadConflicts();
  setInterval(loadConflicts, REFRESH_MS);
});

// ✅ UI filter/sort setup
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
      if (sortBy === field) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      else {
        sortBy = field;
        sortDir = 'asc';
      }
      applyFilters();
    });
  });
}

// ✅ API Load
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
    console.error('❌ Error loading conflicts:', err);
    tbody.innerHTML = '<tr><td colspan="10">Failed to load conflicts.</td></tr>';
  }
}

// ✅ Apply Filter + Sort
function applyFilters() {
  const searchVal = (document.getElementById('conflictSearch')?.value || '').toLowerCase();
  let rows = conflicts.slice();

  switch (currentFilter) {
    case 'active': rows = rows.filter(r => r.phase === 'live'); break;
    case 'concluded': rows = rows.filter(r => r.phase === 'resolved'); break;
    case 'planning': rows = rows.filter(r => r.phase === 'planning'); break;
    case 'resolution': rows = rows.filter(r => r.phase === 'resolved' && r.winner_side); break;
  }

  if (searchVal) {
    rows = rows.filter(r =>
      (r.attacker_alliance || '').toLowerCase().includes(searchVal) ||
      (r.defender_alliance || '').toLowerCase().includes(searchVal) ||
      (r.attacker_kingdom || '').toLowerCase().includes(searchVal) ||
      (r.defender_kingdom || '').toLowerCase().includes(searchVal)
    );
  }

  if (sortBy) {
    rows.sort((a, b) => compareFields(a, b, sortBy));
  }

  renderRows(rows);
}

function compareFields(a, b, field) {
  if (field === 'started_at') {
    const da = a[field] ? new Date(a[field]) : 0;
    const db = b[field] ? new Date(b[field]) : 0;
    return sortDir === 'asc' ? da - db : db - da;
  }

  const valA = (a[field] || '').toString();
  const valB = (b[field] || '').toString();
  return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
}

// ✅ Render table rows
function renderRows(rows) {
  const tbody = document.getElementById('conflictRows');
  if (!tbody) return;

  if (rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10">No conflicts found.</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  rows.forEach(r => {
    const tickPct = r.battle_tick ? Math.min(r.battle_tick * 100 / 12, 100) : 0;
    const progress = `
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width:${tickPct}%;" title="Tick Progress: ${r.battle_tick || 0}/12"></div>
      </div>
    `;
    const phaseClass = `status-${r.phase || 'alert'}`;
    const linkLive = `<a href="battle_live.html?war_id=${r.war_id}">View Battle</a>`;
    const linkRes = r.victor || r.winner_side
      ? ` | <a href="battle_resolution.html?war_id=${r.war_id}">View Resolution</a>` : '';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.war_id}</td>
      <td>${escapeHTML(r.attacker_alliance || r.attacker_kingdom || '')}</td>
      <td>${escapeHTML(r.defender_alliance || r.defender_kingdom || '')}</td>
      <td>${escapeHTML(r.war_type || '')}</td>
      <td>${r.started_at ? new Date(r.started_at).toLocaleDateString() : ''}</td>
      <td class="${phaseClass}">${escapeHTML(r.phase || '')}</td>
      <td>${escapeHTML(r.victor || r.winner_side || '')}</td>
      <td>${progress}</td>
      <td>${r.castle_hp ?? ''}</td>
      <td>${linkLive}${linkRes}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ✅ Safe HTML Escape
function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
