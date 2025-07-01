// Project Name: Thronestead©
// File Name: admin_dashboard.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { escapeHTML, authJsonFetch, authFetch } from './utils.js';

const REFRESH_MS = 30000;

// 🔁 Interval Loader
function setupAutoRefresh() {
  loadDashboardStats();
  loadFlaggedUsers();
  setInterval(() => {
    loadDashboardStats();
    loadFlaggedUsers();
  }, REFRESH_MS);
}

// 📊 Dashboard Stats
async function loadDashboardStats() {
  try {
    const data = await authJsonFetch('/api/admin/stats');
    ['total-users', 'sum-users'].forEach(id => setText(id, data.active_users));
    ['flagged-users', 'sum-flags'].forEach(id => setText(id, data.flagged_users));
    setText('suspicious-activity', data.suspicious_count);
    setText('sum-wars', data.active_wars);
  } catch (e) {
    console.error('⚠️ Dashboard stats error:', e);
  }
}

// 🧑‍💻 Player List
async function loadPlayerList() {
  const q = document.getElementById('search-player')?.value.toLowerCase() || '';
  const status = document.getElementById('status-filter')?.value || '';
  const container = document.getElementById('player-list');
  if (!container) return;

  container.innerHTML = '<p>Loading players...</p>';
  try {
    const url = new URL('/api/admin/search_user', window.location.origin);
    if (q) url.searchParams.set('q', q);
    if (status) url.searchParams.set('status', status);
    const players = await authJsonFetch(url);
    container.innerHTML = players.length ? '' : '<p>No players found.</p>';

    players.forEach(p => {
      const card = document.createElement('div');
      card.className = 'player-card';
      card.innerHTML = `
        <p><strong>${escapeHTML(p.username)}</strong> (${escapeHTML(p.id)})</p>
        <p>Status: ${escapeHTML(p.status)}</p>
        <div class="player-actions">
          ${['flag', 'freeze', 'ban'].map(action =>
            `<button class="admin-btn" data-action="${action}" data-id="${escapeHTML(p.id)}">${capitalize(action)}</button>`
          ).join('')}
        </div>`;
      container.appendChild(card);
    });
  } catch (e) {
    console.error('⚠️ Player list error:', e);
    container.innerHTML = '<p class="error-msg">Failed to fetch players.</p>';
  }
}

// 📝 Audit Logs
async function loadAuditLogs() {
  const container = document.getElementById('log-list');
  if (!container) return;
  container.innerHTML = '<p>Loading logs...</p>';

  try {
    const logs = await authJsonFetch('/api/admin/logs');
    container.innerHTML = logs.length ? '' : '<p>No audit logs found.</p>';

    logs.forEach(log => {
      const entry = document.createElement('div');
      entry.className = 'log-card';
      entry.innerHTML = `
        <p><strong>${escapeHTML(log.action)}</strong> — ${escapeHTML(log.details)}</p>
        <p class="log-time">${new Date(log.created_at).toLocaleString()}</p>`;
      container.appendChild(entry);
    });
  } catch (e) {
    console.error('⚠️ Logs error:', e);
    container.innerHTML = '<p class="error-msg">Failed to fetch audit logs.</p>';
  }
}

// 🚩 Flagged Players
async function loadFlaggedUsers() {
  const container = document.getElementById('flagged-list');
  if (!container) return;
  container.innerHTML = '<p>Loading flagged players...</p>';

  try {
    const rows = await authJsonFetch('/api/admin/flagged_users');
    container.innerHTML = rows.length ? '' : '<p>No flagged users.</p>';

    rows.forEach(row => {
      const card = document.createElement('div');
      card.className = 'flagged-card';
      card.innerHTML = `
        <p><strong>${escapeHTML(row.user_id)}</strong> — ${escapeHTML(row.type)}</p>
        <p>${new Date(row.created_at).toLocaleString()}</p>`;
      container.appendChild(card);
    });
  } catch (e) {
    console.error('❌ Flagged load error:', e);
    container.innerHTML = '<p>Error loading flagged users.</p>';
  }
}

// ⚠️ Realtime Alerts
function initAlertSocket() {
  const container = document.getElementById('alerts');
  if (!container) return;
  container.innerHTML = '';
  const socket = new WebSocket('/api/admin/alerts/live');

  socket.onmessage = ({ data }) => {
    const alert = JSON.parse(data);
    const el = document.createElement('div');
    el.className = 'alert-item';
    el.innerHTML = `<b>${escapeHTML(alert.type)}</b>: ${escapeHTML(alert.message)} <small>${new Date(alert.timestamp).toLocaleString()}</small>`;
    container.prepend(el);
  };

  socket.onerror = err => console.error('❌ Alert socket error:', err);
}

// ✅ Admin Actions
async function handleAdminAction(endpoint, payload, msg) {
  try {
    await postAdminAction(endpoint, payload);
    alert(`✅ ${msg}`);
  } catch (err) {
    console.error('❌ Action failed:', err);
    alert(`❌ Action failed: ${err.message}`);
  }
}

async function postAdminAction(endpoint, payload) {
  const res = await authFetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
}

// 🛠 Admin Utilities
const actions = {
  'toggle-flag-btn': async () => {
    const key = getValue('flag-key');
    const value = getValue('flag-value') === 'true';
    if (!key) return alert('Enter a flag key');
    await handleAdminAction('/api/admin/flags/toggle', { flag_key: key, value }, 'Flag updated');
  },
  'update-kingdom-btn': async () => {
    const id = Number(getValue('kingdom-id'));
    const field = getValue('kingdom-field');
    const value = getValue('kingdom-value');
    if (!id || !field) return alert('Missing field/kingdom');
    await handleAdminAction('/api/admin/kingdom/update_field', { kingdom_id: id, field, value }, 'Kingdom updated');
  },
  'force-end-war-btn': async () => {
    const id = Number(getValue('war-id'));
    if (!id) return alert('Enter war ID');
    await handleAdminAction('/api/admin/war/force_end', { war_id: id }, 'War ended');
  },
  'rollback-tick-btn': async () => {
    const id = Number(getValue('war-id'));
    if (!id) return alert('Enter war ID');
    await handleAdminAction('/api/admin/war/rollback_tick', { war_id: id }, 'Tick rolled back');
  },
  'rollback-btn': async () => {
    const pass = getValue('rollback-password');
    if (!pass) return alert('Enter master password');
    await handleAdminAction('/api/admin/system/rollback', { password: pass }, 'Rollback triggered');
  },
  'create-event': async () => {
    const name = prompt('Event name?');
    if (!name) return;
    await handleAdminAction('/api/admin/events/create', { name }, 'Event created');
  },
  'publish-news-btn': async () => {
    const payload = ['title', 'summary', 'content'].reduce((acc, id) => {
      acc[id] = getValue(`news-${id}`).trim();
      return acc;
    }, {});
    if (!payload.title || !payload.summary || !payload.content) return alert('Fill all news fields');
    await handleAdminAction('/api/admin/news/post', payload, 'News published');
    ['title', 'summary', 'content'].forEach(id => (document.getElementById(`news-${id}`).value = ''));
  }
};

// ✨ UI Bindings
document.addEventListener('DOMContentLoaded', () => {
  loadDashboardStats();
  loadPlayerList();
  initAlertSocket();
  loadFlaggedUsers();
  setupAutoRefresh();

  document.getElementById('search-btn')?.addEventListener('click', loadPlayerList);
  document.getElementById('status-filter')?.addEventListener('change', loadPlayerList);
  document.getElementById('load-logs-btn')?.addEventListener('click', loadAuditLogs);

  Object.entries(actions).forEach(([id, fn]) => {
    document.getElementById(id)?.addEventListener('click', fn);
  });
});

// 🎯 Delegate admin button actions
document.addEventListener('click', async e => {
  if (!e.target.classList.contains('admin-btn')) return;
  const id = e.target.dataset.id;
  const action = e.target.dataset.action;
  const map = {
    flag: ['/api/admin/flag', 'User flagged'],
    freeze: ['/api/admin/freeze', 'User frozen'],
    ban: ['/api/admin/ban', 'User banned']
  };
  if (map[action]) {
    const [url, msg] = map[action];
    await handleAdminAction(url, { player_id: id }, msg);
  }
});

// 🔧 Helpers
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function getValue(id) {
  return document.getElementById(id)?.value || '';
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
