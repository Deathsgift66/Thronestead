// Project Name: Thronestead©
// File Name: conflicts.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML, debounce, jsonFetch, setBarWidths } from './utils.js';

let headers = {};
const REFRESH_MS = 30000;

let conflicts = [];
let currentFilter = 'all';
let sortBy = 'start_date';
let sortDir = 'desc';

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return (window.location.href = 'login.html');
  headers = {
    'Authorization': `Bearer ${session.access_token}`,
    'X-User-ID': session.user.id
  };

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
  if (search) search.addEventListener('input', debounce(applyFilters, 300));

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
    const data = await jsonFetch('/api/conflicts/all', { headers });
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
    case 'active':
      rows = rows.filter(r => r.phase === 'live');
      break;
    case 'planning':
      rows = rows.filter(r => r.phase === 'planning' || r.phase === 'alert');
      break;
    case 'resolution':
      rows = rows.filter(r => r.phase === 'resolved' && !r.victor);
      break;
    case 'concluded':
      rows = rows.filter(r => r.phase === 'resolved' && !!r.victor);
      break;
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
  if (field === 'start_date') {
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
        <div class="progress-bar-fill" data-width="${tickPct}" title="Tick Progress: ${r.battle_tick || 0}/12"></div>
      </div>
    `;
    const phaseClass = `status-${r.phase || 'alert'}`;
    const linkLive = `<a href="battle_live.html?war_id=${r.war_id}">View Battle</a>`;
    const linkRes = r.victor || r.winner_side
      ? ` | <a href="battle_resolution.html?war_id=${r.war_id}">View Resolution</a>` : '';

    const tr = document.createElement('tr');
    tr.classList.add(`row-${(r.phase || '').toLowerCase()}`);
    tr.innerHTML = `
      <td>${r.war_id}</td>
      <td>${escapeHTML(r.attacker_alliance || r.attacker_kingdom || '')}</td>
      <td>${escapeHTML(r.defender_alliance || r.defender_kingdom || '')}</td>
      <td>${escapeHTML(r.war_type || '')}</td>
      <td>${r.start_date ? new Date(r.start_date).toLocaleDateString() : ''}</td>
      <td class="${phaseClass}">${escapeHTML(r.phase || '')}</td>
      <td>${escapeHTML(r.victor || r.winner_side || '')}</td>
      <td>${progress}</td>
      <td>${r.castle_hp ?? ''}</td>
      <td>${linkLive}${linkRes}</td>
    `;
    tr.addEventListener('click', () => openWarModal(r.war_id));
    tbody.appendChild(tr);
  });
  setBarWidths(tbody);
}

// ✅ Open detail modal
async function openWarModal(warId) {
  const modal = document.getElementById('war-detail-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.innerHTML = '<div class="modal-content"><p>Loading...</p></div>';

  try {
    const data = await jsonFetch(`/api/conflicts/${warId}`, { headers });
    const w = data.war || {};
    const tickPct = w.battle_tick ? Math.min(w.battle_tick * 100 / 12, 100) : 0;
    const participants = [w.alliance_a_name, w.alliance_b_name].filter(Boolean);

    modal.innerHTML = `
      <div class="modal-content">
        <h3 id="warDetailHeader">${escapeHTML(w.alliance_a_name || '')} vs ${escapeHTML(w.alliance_b_name || '')}</h3>
        <div class="progress-bar-bg"><div class="progress-bar-fill" data-width="${tickPct}"></div></div>
        <p>Phase: ${escapeHTML(w.phase || '')}</p>
        <p>Castle HP: ${w.castle_hp ?? ''}</p>
        <p>Score: ${w.attacker_score ?? 0} - ${w.defender_score ?? 0}</p>
        <p>Victor: ${escapeHTML(w.victor || '')}</p>
        <ul>${participants.map(p => `<li>${escapeHTML(p)}</li>`).join('')}</ul>
        <button type="button" class="action-btn" id="war-detail-close-btn">Close</button>
      </div>`;

    setBarWidths(modal);

    modal.querySelector('#war-detail-close-btn').addEventListener('click', closeWarModal);
  } catch (err) {
    console.error('Failed to load war details:', err);
    modal.innerHTML = `<div class="modal-content"><p>Failed to load war details.</p><button type="button" class="action-btn" id="war-detail-close-btn">Close</button></div>`;
    modal.querySelector('#war-detail-close-btn').addEventListener('click', closeWarModal);
  }
}

function closeWarModal() {
  const modal = document.getElementById('war-detail-modal');
  if (modal) modal.classList.add('hidden');
}

// ✅ Safe HTML Escape
