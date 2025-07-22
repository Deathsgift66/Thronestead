// Project Name: Thronestead©
// File Name: admin_dashboard.js
// Version: 7/18/2025
// Developer: Deathsgift66

import {
  escapeHTML,
  authJsonFetch,
  authFetch,
  showToast,
  debounce,
  updateElementText,
  formatTimestamp
} from '/Javascript/core_utils.js';
import {
  initCsrf,
  rotateCsrfToken,
  getCsrfToken
} from '/Javascript/security/csrf.js';

window.requireAdmin = true;
const adminMeta = document.querySelector('meta[name="require-admin"]');
if (!adminMeta) {
  const meta = document.createElement('meta');
  meta.name = 'require-admin';
  meta.content = 'true';
  document.head.appendChild(meta);
} else {
  adminMeta.content = 'true';
}

const REFRESH_MS = 30000;
initCsrf();
setInterval(rotateCsrfToken, 15 * 60 * 1000);

const sanitizeField = str => str.replace(/[^A-Za-z0-9_.-]/g, '');
const sanitizeValue = str => str.replace(/[<>]/g, '');

function setupAutoRefresh() {
  loadDashboardStats();
  loadFlaggedUsers();
  setInterval(() => {
    if (document.visibilityState !== 'visible') return;
    loadDashboardStats();
    loadFlaggedUsers();
  }, REFRESH_MS);
}

let lastStats = {};
let lastStatsTime = 0;
async function loadDashboardStats() {
  try {
    const data = await authJsonFetch(`/api/admin/stats?v=${Date.now()}`);
    if (JSON.stringify(data) === JSON.stringify(lastStats)) return;
    lastStats = data;
    ['total-users', 'total-users-card'].forEach(id => updateElementText(id, data.active_users));
    ['flagged-users', 'sum-flags'].forEach(id => updateElementText(id, data.flagged_users));
    updateElementText('suspicious-activity', data.suspicious_count);
    updateElementText('sum-wars', data.active_wars);
    lastStatsTime = Date.now();
    updateElementText('stats-updated', formatTimestamp(lastStatsTime));
  } catch (e) {
    console.error('⚠️ Dashboard stats error:', e);
  }
}

async function loadPlayerList(page = 1) {
  const q = document.getElementById('search-player')?.value.toLowerCase() || '';
  const status = document.getElementById('status-filter')?.value || '';
  const sort = document.getElementById('sort-order')?.value || 'username-asc';
  const container = document.getElementById('player-list');
  if (!container) return;
  container.textContent = 'Loading...';
  try {
    const url = new URL('/api/admin/search_user', window.location.origin);
    if (q) url.searchParams.set('q', encodeURIComponent(q));
    if (status) url.searchParams.set('status', encodeURIComponent(status));
    url.searchParams.set('page', page);
    let players = await authJsonFetch(url);
    players = players.sort((a, b) => sort === 'username-desc'
      ? b.username.localeCompare(a.username)
      : a.username.localeCompare(b.username));
    container.innerHTML = '';
    if (!players.length) {
      container.innerHTML = '<p>No players found.</p>';
      return;
    }
    const frag = document.createDocumentFragment();
    players.forEach(p => {
      const card = document.createElement('div');
      card.className = 'player-card';
      card.innerHTML = `
        <p><strong>${escapeHTML(p.username)}</strong> (${escapeHTML(p.id)})</p>
        <p>Status: ${escapeHTML(p.status)}</p>
        <div class="player-actions">
          ${['flag', 'freeze', 'ban'].map(action => `
            <button class="admin-btn" data-action="${action}" data-id="${escapeHTML(p.id)}">
              ${action.charAt(0).toUpperCase() + action.slice(1)}
            </button>`).join('')}
        </div>`;
      frag.appendChild(card);
    });
    container.appendChild(frag);
  } catch (e) {
    console.error('⚠️ Player list error:', e);
    container.innerHTML = '<p class="error-msg">Failed to fetch players.</p>';
  }
}

// -------------------------
// ⚠️ Helper Utilities
// -------------------------
async function postAdminAction(endpoint, payload) {
  const res = await authFetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
}

async function handleAdminAction(endpoint, payload, msg, btn) {
  try {
    await postAdminAction(endpoint, payload);
    showToast(`✅ ${msg}`, 'success');
    if (btn) {
      btn.classList.add('flash-success');
      setTimeout(() => btn.classList.remove('flash-success'), 600);
    }
  } catch (err) {
    console.error('❌ Action failed:', err);
    showToast(`Action failed: ${err.message}`, 'error');
  }
}

function buildAuditParams() {
  const params = new URLSearchParams();
  const type = document.getElementById('log-type')?.value.trim();
  const user = document.getElementById('log-user')?.value.trim();
  const start = document.getElementById('log-start')?.value;
  const end = document.getElementById('log-end')?.value;
  if (type) params.set('search', type);
  if (user) params.set('user_id', user);
  if (start) params.set('start_date', start);
  if (end) params.set('end_date', end);
  return params;
}

// -------------------------
// 📃 Audit Logs
// -------------------------
async function renderAuditLogs() {
  const container = document.getElementById('log-list');
  if (!container) return;
  container.textContent = 'Loading...';
  try {
    const url = new URL('/api/admin/audit/logs', window.location.origin);
    url.search = buildAuditParams().toString();
    const logs = await authJsonFetch(url);
    container.innerHTML = '';
    if (!logs.length) {
      container.innerHTML = '<p>No logs found.</p>';
      return;
    }
    const frag = document.createDocumentFragment();
    logs.forEach(l => {
      const div = document.createElement('div');
      div.className = 'log-card';
      div.innerHTML = `
        <p><strong>${escapeHTML(l.action)}</strong> — ${escapeHTML(l.details || '')}</p>
        <p class="log-time">${formatTimestamp(l.created_at)}</p>`;
      frag.appendChild(div);
    });
    container.appendChild(frag);
  } catch (e) {
    console.error('⚠️ Log fetch error:', e);
    container.innerHTML = '<p class="error-msg">Failed to fetch logs.</p>';
  }
}

async function exportLogsCSV() {
  try {
    const params = buildAuditParams();
    params.set('format', 'csv');
    const url = `/api/admin/audit/logs?${params}`;
    const res = await authFetch(url);
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const href = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = href;
    a.download = 'audit_logs.csv';
    a.click();
    URL.revokeObjectURL(href);
    showToast('CSV exported', 'success');
  } catch (err) {
    console.error('CSV export failed:', err);
    showToast('Export failed', 'error');
  }
}

async function exportLogsJSON() {
  try {
    const params = buildAuditParams();
    const url = `/api/admin/audit/logs?${params}`;
    const res = await authFetch(url);
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const href = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = href;
    a.download = 'audit_logs.json';
    a.click();
    URL.revokeObjectURL(href);
    showToast('JSON exported', 'success');
  } catch (err) {
    console.error('JSON export failed:', err);
    showToast('Export failed', 'error');
  }
}

// -------------------------
// 🚨 Live Alerts
// -------------------------
let alertSocket = null;
async function initAlertSocket() {
  try {
    const { url } = await authJsonFetch('/api/admin/alerts/connect', {
      method: 'POST',
      headers: { 'X-CSRF-Token': getCsrfToken() }
    });
    alertSocket = new WebSocket(url);
    const statusEl = document.getElementById('alert-status');
    alertSocket.addEventListener('open', () => {
      statusEl && (statusEl.textContent = '✅ Connected');
    });
    alertSocket.addEventListener('close', () => {
      statusEl && (statusEl.textContent = '❌ Disconnected');
    });
    alertSocket.addEventListener('message', e => {
      try {
        const data = JSON.parse(e.data);
        appendAlert(data);
      } catch {}
    });
  } catch (err) {
    console.error('Alert socket init failed:', err);
  }
}

function appendAlert(alert) {
  const container = document.getElementById('alerts');
  if (!container) return;
  const div = document.createElement('div');
  div.className = 'alert-item';
  div.innerHTML = `
    <p><strong>${escapeHTML(alert.type || alert.alert_type || 'alert')}</strong> — ${escapeHTML(alert.message || alert.details || '')}</p>
    <small>${formatTimestamp(alert.timestamp || alert.created_at)}</small>`;
  container.prepend(div);
}

// -------------------------
// 🔨 Flag & War Tools
// -------------------------
async function loadFlaggedUsers() {
  const container = document.getElementById('flagged-list');
  if (!container) return;
  container.textContent = 'Loading...';
  try {
    const rows = await authJsonFetch('/api/admin/flagged');
    container.innerHTML = '';
    if (!rows.length) {
      container.innerHTML = '<p>No flagged users.</p>';
      return;
    }
    const frag = document.createDocumentFragment();
    rows.forEach(r => {
      const card = document.createElement('div');
      card.className = 'flagged-card';
      card.innerHTML = `
        <p><strong>${escapeHTML(r.user_id)}</strong> — ${escapeHTML(r.type)}</p>
        <small>${formatTimestamp(r.created_at)}</small>`;
      frag.appendChild(card);
    });
    container.appendChild(frag);
  } catch (err) {
    console.error('Flagged user load failed:', err);
    container.innerHTML = '<p class="error-msg">Error loading flagged users.</p>';
  }
}

async function loadFlags() {
  const body = document.querySelector('#flag-table tbody');
  if (!body) return;
  body.innerHTML = '<tr><td colspan="2">Loading…</td></tr>';
  try {
    const rows = await authJsonFetch('/api/admin/flags');
    body.innerHTML = '';
    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="2">No flags</td></tr>';
      return;
    }
    const frag = document.createDocumentFragment();
    rows.forEach(f => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${escapeHTML(f.flag_key)}</td><td>${escapeHTML(String(f.flag_value))}</td>`;
      frag.appendChild(tr);
    });
    body.appendChild(frag);
  } catch (err) {
    console.error('Load flags failed:', err);
    body.innerHTML = '<tr><td colspan="2">Error loading flags</td></tr>';
  }
}

const actions = {
  'toggle-flag-btn': btn => {
    const key = sanitizeField(document.getElementById('flag-key').value.trim());
    const value = document.getElementById('flag-value').value === 'true';
    if (!key) return showToast('Enter a flag key', 'error');
    handleAdminAction('/api/admin/flags/toggle', { flag_key: key, value }, 'Flag updated', btn).then(loadFlags);
  },
  'update-kingdom-btn': btn => {
    const id = Number(document.getElementById('kingdom-id').value.trim());
    const field = sanitizeField(document.getElementById('kingdom-field').value.trim());
    const value = sanitizeValue(document.getElementById('kingdom-value').value.trim());
    if (!id || !field) return showToast('Missing field/kingdom', 'error');
    handleAdminAction('/api/admin/kingdom/update_field', { kingdom_id: id, field, value }, 'Kingdom updated', btn);
  },
  'force-end-war-btn': btn => {
    const id = Number(document.getElementById('war-id').value.trim());
    if (!id) return showToast('Enter war ID', 'error');
    handleAdminAction('/api/admin/wars/force_end', { war_id: id }, 'War ended', btn);
  },
  'rollback-tick-btn': btn => {
    const id = Number(document.getElementById('war-id').value.trim());
    if (!id) return showToast('Enter war ID', 'error');
    handleAdminAction('/api/admin/wars/rollback_tick', { war_id: id }, 'Tick rolled back', btn);
  },
  'create-event': btn => {
    const dlg = document.getElementById('create-event-dialog');
    dlg.showModal();
    const nameInput = dlg.querySelector('#event-name');
    nameInput.focus();
    const confirm = dlg.querySelector('.confirm');
    const cancel = dlg.querySelector('.cancel');
    const cleanup = () => {
      confirm.removeEventListener('click', onConfirm);
      cancel.removeEventListener('click', onCancel);
    };
    const onConfirm = async () => {
      dlg.close();
      cleanup();
      const name = nameInput.value.trim();
      if (!name) return showToast('Event name required', 'error');
      await handleAdminAction('/api/admin/events/create', { name }, 'Event created', btn);
      nameInput.value = '';
    };
    const onCancel = () => { dlg.close(); cleanup(); };
    confirm.addEventListener('click', onConfirm, { once: true });
    cancel.addEventListener('click', onCancel, { once: true });
  },
  'publish-news-btn': btn => {
    const payload = ['title', 'summary', 'content'].reduce((acc, id) => {
      acc[id] = document.getElementById(`news-${id}`).value.trim();
      return acc;
    }, {});
    if (!payload.title || !payload.summary || !payload.content) {
      return showToast('Fill all news fields', 'error');
    }
    handleAdminAction('/api/admin/news/post', payload, 'News published', btn);
    ['title', 'summary', 'content'].forEach(id => (document.getElementById(`news-${id}`).value = ''));
  }
};

document.addEventListener('click', e => {
  if (!e.target.matches('.admin-btn')) return;
  const action = e.target.dataset.action;
  const id = e.target.dataset.id;
  if (!action || !id) return;
  handleAdminAction(`/api/admin/${action}`, { player_id: id }, `${action} executed`, e.target);
});

export function init() {
  loadDashboardStats();
  loadPlayerList();
  initAlertSocket();
  loadFlaggedUsers();
  loadFlags();
  setupAutoRefresh();

  const debouncedLoad = debounce(() => loadPlayerList(1), 400);
  document.getElementById('search-btn')?.addEventListener('click', debouncedLoad);
  document.getElementById('search-player')?.addEventListener('keypress', e => e.key === 'Enter' && debouncedLoad());
  document.getElementById('status-filter')?.addEventListener('change', debouncedLoad);
  document.getElementById('load-logs-btn')?.addEventListener('click', renderAuditLogs);
  document.getElementById('export-csv')?.addEventListener('click', exportLogsCSV);
  document.getElementById('export-json')?.addEventListener('click', exportLogsJSON);
  Object.entries(actions).forEach(([id, fn]) => {
    document.getElementById(id)?.addEventListener('click', () => fn(document.getElementById(id)));
  });

  window.adminDashboardReady = true;
}

document.addEventListener('DOMContentLoaded', init);

window.onerror = (msg, src, line, col, err) => {
  console.error('Window error', msg, err);
};
window.onunhandledrejection = e => {
  console.error('Promise rejection', e.reason);
};
