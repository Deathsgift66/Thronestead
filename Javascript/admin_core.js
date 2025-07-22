// Project Name: Thronestead©
// File Name: admin_core.js
// Consolidated admin module

export * from './admin_dashboard.js';
export * from './admin_emergency_tools.js';
export * from './admin_alerts.js';

import { escapeHTML, fragmentFrom, authJsonFetch } from './core_utils.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';
import { getEnvVar } from './env.js';
import { supabase } from './supabaseClient.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');
let eventSource;
let offset = 0;
let connectedAt = 0;
let sseTimer;
let playerChannel;

export async function initAuditLogPage() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  try {
    await checkAdmin();
  } catch {
    window.location.href = 'overview.html';
    return;
  }
  await authJsonFetch('/api/admin/audit-log/view', { method: 'POST' });

  const form = document.getElementById('audit-filter-form');
  if (form) {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      await loadAuditLog();
    });
  }

  document.getElementById('export-csv')?.addEventListener('click', () => {
    window.open(`/api/admin/audit/logs?${buildExportQuery()}&format=csv`, '_blank');
  });
  document.getElementById('export-json')?.addEventListener('click', () => {
    window.open(`/api/admin/audit/logs?${buildExportQuery()}&format=json`, '_blank');
  });
  document.getElementById('load-more-btn')?.addEventListener('click', () => loadAuditLog(false));

  await loadAuditLog();

  try {
    const statusEl = document.getElementById('sse-status');
    eventSource = new EventSource(`${API_BASE_URL}/api/admin/audit-log/stream`);
    eventSource.onopen = () => {
      connectedAt = Date.now();
      updateSseStatus();
      if (sseTimer) clearInterval(sseTimer);
      sseTimer = setInterval(updateSseStatus, 1000);
    };
    eventSource.onmessage = ev => {
      const log = JSON.parse(ev.data);
      prependLogRow(log);
    };
    eventSource.onerror = () => {
      connectedAt = 0;
      updateSseStatus();
    };
    if (statusEl) statusEl.textContent = 'SSE Connected';
  } catch (err) {
    console.error('SSE connection failed', err);
    updateSseStatus();
  }

  window.addEventListener('beforeunload', () => {
    if (eventSource) eventSource.close();
  });
  applyKingdomLinks();
}

async function loadAuditLog(reset = true) {
  const tbody = document.getElementById('audit-log-body');
  const user = document.getElementById('filter-user')?.value.trim();
  const action = document.getElementById('filter-action')?.value.trim();
  const from = document.getElementById('filter-from')?.value;
  const to = document.getElementById('filter-to')?.value;
  const limit = document.getElementById('filter-limit')?.value || 100;

  if (user && !/^[\w-]{36}$/.test(user)) {
    alert('Invalid UUID format');
    return;
  }

  if (reset) {
    offset = 0;
    if (tbody) tbody.innerHTML = '<tr><td colspan="4">Loading audit log...</td></tr>';
  }

  try {
    const params = new URLSearchParams();
    if (user) params.append('user_id', user);
    if (action) params.append('action', action);
    if (from) params.append('date_from', from);
    if (to) params.append('date_to', to);
    params.append('limit', limit);
    params.append('offset', offset);

    const data = await authJsonFetch(`/api/admin/audit-log?${params.toString()}`);

    if (reset && tbody) tbody.innerHTML = '';

    if (!data.logs || data.logs.length === 0) {
      if (reset && tbody) {
        tbody.innerHTML = '<tr><td colspan="4">No audit log entries found.</td></tr>';
      }
      const btn = document.getElementById('load-more-btn');
      if (btn) btn.style.display = 'none';
      return;
    }

    data.logs.forEach(log => {
      const row = document.createElement('tr');
      const details = formatDetails(log.details);
      row.innerHTML = `
        <td>${formatTimestamp(log.created_at)}</td>
        <td>${escapeHTML(log.action)}</td>
        <td>${escapeHTML(log.user_id || '')}</td>
        <td>${details}</td>
      `;
      tbody.appendChild(row);
    });

    offset += data.logs.length;
    const btn = document.getElementById('load-more-btn');
    if (btn) btn.style.display = data.logs.length >= limit ? '' : 'none';
  } catch (err) {
    console.error('❌ Error fetching audit log data:', err);
    if (reset && tbody) {
      tbody.innerHTML = '<tr><td colspan="4">Failed to load audit log.</td></tr>';
    }
  }
  applyKingdomLinks();
}

function prependLogRow(log) {
  const tbody = document.getElementById('audit-log-body');
  const row = document.createElement('tr');
  const details = formatDetails(log.details);
  row.innerHTML = `
    <td>${formatTimestamp(log.created_at)}</td>
    <td>${escapeHTML(log.action)}</td>
    <td>${escapeHTML(log.user_id || '')}</td>
    <td>${details}</td>
  `;
  tbody.prepend(row);
  if (tbody.children.length > 100) {
    tbody.removeChild(tbody.lastChild);
  }
}

function formatTimestamp(timestamp) {
  if (!timestamp) return 'Unknown';
  const date = new Date(timestamp);
  return date.toLocaleString(undefined, {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}

function tryParseJSON(str) {
  try { return JSON.parse(str); } catch { return null; }
}

function renderKeyValueTable(obj) {
  return '<table>' +
    Object.entries(obj).map(([k, v]) => `<tr><th>${escapeHTML(k)}</th><td>${escapeHTML(String(v))}</td></tr>`).join('') +
    '</table>';
}

function formatDetails(details) {
  const parsed = tryParseJSON(details);
  return parsed && typeof parsed === 'object' ? renderKeyValueTable(parsed) : escapeHTML(details);
}

function buildExportQuery() {
  const user = document.getElementById('filter-user')?.value.trim();
  const action = document.getElementById('filter-action')?.value.trim();
  const from = document.getElementById('filter-from')?.value;
  const to = document.getElementById('filter-to')?.value;
  const params = new URLSearchParams();
  if (user) params.append('user_id', user);
  if (action) params.append('search', action);
  if (from) params.append('start_date', from);
  if (to) params.append('end_date', to);
  return params.toString();
}

function checkAdmin() {
  return authJsonFetch('/api/admin/check-admin');
}

function updateSseStatus() {
  const el = document.getElementById('sse-status');
  if (!el) return;
  if (connectedAt) {
    const secs = Math.floor((Date.now() - connectedAt) / 1000);
    el.textContent = `SSE Connected (${secs}s)`;
  } else {
    el.textContent = 'SSE Disconnected';
  }
}

export async function initPlayerManagementPage() {
  await loadPlayerTable();

  document.getElementById('search-button')?.addEventListener('click', loadPlayerTable);
  document.getElementById('search-reset')?.addEventListener('click', () => {
    const input = document.getElementById('search-input');
    if (input) input.value = '';
    loadPlayerTable();
  });

  const bulkActions = {
    'bulk-ban': 'ban',
    'bulk-flag': 'flag',
    'bulk-logout': 'logout',
    'bulk-reset-password': 'reset_password'
  };

  Object.entries(bulkActions).forEach(([btnId, action]) => {
    document.getElementById(btnId)?.addEventListener('click', () => handleBulkAction(action));
  });

  document.getElementById('modal-close-btn')?.addEventListener('click', () =>
    document.getElementById('admin-modal')?.classList.add('hidden')
  );

  playerChannel = supabase
    .channel('players')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'users' }, loadPlayerTable)
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (playerChannel) playerChannel.unsubscribe();
  });
}

async function loadPlayerTable() {
  const tableBody = document.querySelector('#player-table tbody');
  const query = document.getElementById('search-input')?.value.trim() || '';
  tableBody.innerHTML = "<tr><td colspan='8'>Loading players...</td></tr>";

  try {
    const { players } = await authJsonFetch(`/api/admin/players?search=${encodeURIComponent(query)}`);

    tableBody.innerHTML = players?.length
      ? ''
      : "<tr><td colspan='8'>No players found.</td></tr>";

    const rows = fragmentFrom(players, player => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><input type="checkbox" class="player-select" data-id="${player.user_id}"></td>
        <td>${escapeHTML(player.user_id)}</td>
        <td>${escapeHTML(player.username)}</td>
        <td>${escapeHTML(player.email)}</td>
        <td>${escapeHTML(player.kingdom_name)}</td>
        <td>${escapeHTML(player.vip_tier)}</td>
        <td>${escapeHTML(player.status)}</td>
        <td>
          <button class="action-btn flag-btn" data-id="${player.user_id}">Flag</button>
          <button class="action-btn freeze-btn" data-id="${player.user_id}">Freeze</button>
          <button class="action-btn ban-btn" data-id="${player.user_id}">Ban</button>
          <button class="action-btn history-btn" data-id="${player.user_id}">History</button>
        </td>
      `;
      return row;
    });
    tableBody.appendChild(rows);

    rebindActionButtons();
  } catch (err) {
    console.error('❌ Error loading player table:', err);
    tableBody.innerHTML = "<tr><td colspan='8'>Failed to load players.</td></tr>";
  }
}

function rebindActionButtons() {
  const bindAction = (selector, actionName) => {
    document.querySelectorAll(selector).forEach(btn =>
      btn.addEventListener('click', () => showModalConfirm(`${capitalize(actionName)} Player`, btn.dataset.id, actionName))
    );
  };

  bindAction('.flag-btn', 'flag');
  bindAction('.freeze-btn', 'freeze');
  bindAction('.ban-btn', 'ban');
  bindAction('.history-btn', 'history');
}

async function handleBulkAction(action) {
  const selected = Array.from(document.querySelectorAll('.player-select:checked')).map(cb => cb.dataset.id);
  if (!selected.length) return alert('Please select at least one player.');
  if (!confirm(`Perform "${action}" on ${selected.length} players?`)) return;

  try {
    const result = await authJsonFetch('/api/admin/bulk_action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, player_ids: selected })
    });

    alert(result.message || `Bulk "${action}" completed.`);
    await loadPlayerTable();
  } catch (err) {
    console.error(`❌ Bulk ${action} failed:`, err);
    alert(`Failed to perform "${action}".`);
  }
}

async function showModalConfirm(title, userId, action) {
  const modal = document.getElementById('admin-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalBody = document.getElementById('modal-body');
  const confirmBtn = document.getElementById('modal-confirm-btn');

  modalTitle.textContent = title;
  modalBody.innerHTML = `Are you sure you want to <strong>${escapeHTML(action)}</strong> player ID <strong>${escapeHTML(userId)}</strong>?`;

  modal.classList.remove('hidden');

  const newConfirmBtn = confirmBtn.cloneNode(true);
  confirmBtn.replaceWith(newConfirmBtn);

  newConfirmBtn.addEventListener('click', async () => {
    try {
      const result = await authJsonFetch('/api/admin/player_action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, player_id: userId })
      });

      alert(result.message || `Action "${action}" completed.`);
      modal.classList.add('hidden');
      await loadPlayerTable();
    } catch (err) {
      console.error(`❌ ${action} failed:`, err);
      alert(`Failed to ${action}.`);
    }
  });
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
