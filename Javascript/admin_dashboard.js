// Project Name: Thronestead©
// File Name: admin_dashboard.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { escapeHTML } from './utils.js';

const REFRESH_MS = 30000;


// 📊 Dashboard Stats
async function loadDashboardStats() {
  try {
    const res = await fetch('https://thronestead.onrender.com/api/admin/stats');
    if (!res.ok) throw new Error('Failed to fetch stats');
    const data = await res.json();
    document.getElementById('total-users').textContent = data.active_users;
    document.getElementById('flagged-users').textContent = data.flagged_users;
    document.getElementById('suspicious-activity').textContent = data.suspicious_count;
    document.getElementById('sum-users').textContent = data.active_users;
    document.getElementById('sum-flags').textContent = data.flagged_users;
    document.getElementById('sum-wars').textContent = data.active_wars;
  } catch (error) {
    console.error('⚠️ Failed to load dashboard stats:', error);
  }
}

// 🧑‍💻 Player List
async function loadPlayerList() {
  const search = document.getElementById('search-player')?.value.toLowerCase() || '';
  const status = document.getElementById('status-filter')?.value || '';
  const container = document.getElementById('player-list');
  if (!container) return;
  container.innerHTML = '<p>Loading players...</p>';

  try {
    const url = new URL('https://thronestead.onrender.com/api/admin/search_user', window.location.origin);
    url.searchParams.set('q', search);
    if (status) url.searchParams.set('status', status);
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch players');
    const players = await res.json();

    container.innerHTML = players.length ? '' : '<p>No players found.</p>';

    players.forEach(player => {
      const card = document.createElement('div');
      card.className = 'player-card';
      card.innerHTML = `
        <p><strong>${escapeHTML(player.username)}</strong> (${escapeHTML(player.id)})</p>
        <p>Status: ${escapeHTML(player.status)}</p>
        <div class="player-actions">
          <button onclick="flagUser('${escapeHTML(player.id)}')">Flag</button>
          <button onclick="freezeUser('${escapeHTML(player.id)}')">Freeze</button>
          <button onclick="banUser('${escapeHTML(player.id)}')">Ban</button>
        </div>`;
      container.appendChild(card);
    });
  } catch (err) {
    console.error('⚠️ Failed to load player list:', err);
    container.innerHTML = '<p class="error-msg">Failed to fetch players.</p>';
  }
}

// 📝 Audit Logs
async function loadAuditLogs() {
  const container = document.getElementById('log-list');
  if (!container) return;
  container.innerHTML = '<p>Loading logs...</p>';

  try {
    const res = await fetch('https://thronestead.onrender.com/api/admin/logs');
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    const logs = await res.json();

    container.innerHTML = logs.length
      ? ''
      : '<p>No audit logs found.</p>';

    logs.forEach(log => {
      const entry = document.createElement('div');
      entry.className = 'log-card';
      entry.innerHTML = `
        <p><strong>${escapeHTML(log.action)}</strong> — ${escapeHTML(log.details)}</p>
        <p class="log-time">${new Date(log.created_at).toLocaleString()}</p>`;
      container.appendChild(entry);
    });
  } catch (err) {
    console.error('⚠️ Failed to load audit logs:', err);
    container.innerHTML = '<p class="error-msg">Failed to fetch audit logs.</p>';
  }
}

// 🚩 Flagged Players
async function loadFlaggedUsers() {
  const container = document.getElementById('flagged-list');
  if (!container) return;
  container.innerHTML = '<p>Loading flagged players...</p>';

  try {
    const res = await fetch('https://thronestead.onrender.com/api/admin/flagged_users');
    if (!res.ok) throw new Error('Failed to fetch flagged users');
    const rows = await res.json();

    container.innerHTML = rows.length
      ? ''
      : '<p>No flagged users.</p>';

    rows.forEach(row => {
      const card = document.createElement('div');
      card.className = 'flagged-card';
      card.innerHTML = `
        <p><strong>${escapeHTML(row.player_id)}</strong> — ${escapeHTML(row.alert_type)}</p>
        <p>${new Date(row.created_at).toLocaleString()}</p>`;
      container.appendChild(card);
    });
  } catch (err) {
    console.error('Failed to load flagged users:', err);
    container.innerHTML = '<p>Error loading flagged users.</p>';
  }
}

// ⚠️ Alerts
function initAlertSocket() {
  const container = document.getElementById('alerts');
  if (!container) return;
  container.innerHTML = '';
  const socket = new WebSocket('https://thronestead.onrender.com/api/admin/alerts/live');
  socket.onmessage = event => {
    const alert = JSON.parse(event.data);
    const el = document.createElement('div');
    el.classList.add('alert-item');
    el.innerHTML = `<b>${escapeHTML(alert.type)}</b>: ${escapeHTML(alert.message)} <small>${new Date(alert.timestamp).toLocaleString()}</small>`;
    container.prepend(el);
  };
  socket.onerror = err => console.error('Alert socket error:', err);
}

// ✅ Admin Actions
window.flagUser = async userId => handleAdminAction('https://thronestead.onrender.com/api/admin/flag', { player_id: userId }, 'User flagged');
window.freezeUser = async userId => handleAdminAction('https://thronestead.onrender.com/api/admin/freeze', { player_id: userId }, 'User frozen');
window.banUser = async userId => handleAdminAction('https://thronestead.onrender.com/api/admin/ban', { player_id: userId }, 'User banned');
window.showAlertDetails = alertId => alert(`📋 Detailed view for Alert ID: ${alertId} will load here.`);

async function handleAdminAction(endpoint, payload, successMsg) {
  try {
    await postAdminAction(endpoint, payload);
    alert(`✅ ${successMsg}`);
  } catch (err) {
    console.error('❌ Action failed:', err);
    alert('❌ Action failed: ' + err.message);
  }
}

async function postAdminAction(endpoint, payload) {
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
}

// 🛠 Admin Utilities
async function toggleFlag() {
  const key = document.getElementById('flag-key')?.value;
  const val = document.getElementById('flag-value')?.value === 'true';
  if (!key) return alert('Enter a flag key');
  await handleAdminAction('https://thronestead.onrender.com/api/admin/flags/toggle', { flag_key: key, value: val }, 'Flag updated');
}

async function updateKingdom() {
  const kid = document.getElementById('kingdom-id')?.value;
  const field = document.getElementById('kingdom-field')?.value;
  const value = document.getElementById('kingdom-value')?.value;
  if (!kid || !field) return alert('Missing field/kingdom');
  await handleAdminAction('https://thronestead.onrender.com/api/admin/kingdom/update_field', {
    kingdom_id: Number(kid),
    field,
    value
  }, 'Kingdom updated');
}

async function forceEndWar() {
  const wid = document.getElementById('war-id')?.value;
  if (!wid) return alert('Enter war ID');
  await handleAdminAction('https://thronestead.onrender.com/api/admin/war/force_end', { war_id: Number(wid) }, 'War ended');
}

async function rollbackCombatTick() {
  const wid = document.getElementById('war-id')?.value;
  if (!wid) return alert('Enter war ID');
  await handleAdminAction('https://thronestead.onrender.com/api/admin/war/rollback_tick', { war_id: Number(wid) }, 'Tick rolled back');
}

async function rollbackDatabase() {
  const pass = document.getElementById('rollback-password')?.value;
  if (!pass) return alert('Enter master password');
  await handleAdminAction('https://thronestead.onrender.com/api/admin/system/rollback', { password: pass }, 'Rollback triggered');
}

async function createGlobalEvent() {
  const name = prompt('Event name?');
  if (!name) return;
  await handleAdminAction('https://thronestead.onrender.com/api/admin/events/create', { name }, 'Event created');
}

async function publishNews() {
  const title = document.getElementById('news-title')?.value.trim();
  const summary = document.getElementById('news-summary')?.value.trim();
  const content = document.getElementById('news-content')?.value.trim();
  if (!title || !summary || !content) return alert('Fill all news fields');
  await handleAdminAction('https://thronestead.onrender.com/api/admin/news/post', { title, summary, content }, 'News published');
  document.getElementById('news-title').value = '';
  document.getElementById('news-summary').value = '';
  document.getElementById('news-content').value = '';
}

// 🧩 Initialize DOM Hooks
document.addEventListener('DOMContentLoaded', () => {
  loadDashboardStats();
  loadPlayerList();
  initAlertSocket();
  loadFlaggedUsers();

  setInterval(() => {
    loadDashboardStats();
    loadFlaggedUsers();
  }, REFRESH_MS);

  document.getElementById('search-btn')?.addEventListener('click', loadPlayerList);
  document.getElementById('status-filter')?.addEventListener('change', loadPlayerList);
  document.getElementById('load-logs-btn')?.addEventListener('click', loadAuditLogs);
  document.getElementById('toggle-flag-btn')?.addEventListener('click', toggleFlag);
  document.getElementById('update-kingdom-btn')?.addEventListener('click', updateKingdom);
  document.getElementById('force-end-war-btn')?.addEventListener('click', forceEndWar);
  document.getElementById('rollback-tick-btn')?.addEventListener('click', rollbackCombatTick);
  document.getElementById('rollback-btn')?.addEventListener('click', rollbackDatabase);
  document.getElementById('create-event')?.addEventListener('click', createGlobalEvent);
  document.getElementById('publish-news-btn')?.addEventListener('click', publishNews);
});
