// Project Name: Kingmakers Rise©
// File Name: admin_dashboard.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

const REFRESH_MS = 30000;

// 🔐 Prevent XSS via innerHTML
function escapeHTML(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// 📊 Dashboard Stats
async function loadDashboardStats() {
  try {
    const [users, flagged, audit] = await Promise.all([
      supabase.from('users').select('id'),
      supabase.from('account_alerts').select('id'),
      supabase.from('audit_log').select('id'),
    ]);
    document.getElementById('total-users').textContent = users.data?.length ?? 0;
    document.getElementById('flagged-users').textContent = flagged.data?.length ?? 0;
    document.getElementById('suspicious-activity').textContent = audit.data?.length ?? 0;
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
    const { data: players, error } = await supabase.from('users').select('*');
    if (error) throw new Error(error.message);

    const filtered = players.filter(p =>
      p.username?.toLowerCase().includes(search) &&
      (!status || p.status === status)
    );

    container.innerHTML = filtered.length
      ? ''
      : '<p>No players found.</p>';

    filtered.forEach(player => {
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
    const res = await fetch('/api/admin/audit/logs');
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
    const res = await fetch('/api/admin/flagged');
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
async function loadAccountAlerts() {
  const container = document.getElementById('alerts');
  if (!container) return;
  container.innerHTML = '<p>Loading alerts...</p>';

  try {
    const { data: alerts, error } = await supabase
      .from('account_alerts')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw new Error(error.message);

    container.innerHTML = alerts.length
      ? ''
      : '<p>No alerts found.</p>';

    alerts.forEach(alert => {
      const item = document.createElement('div');
      item.className = 'alert-item';
      item.innerHTML = `
        <p><strong>${escapeHTML(alert.alert_type)}</strong> — ${escapeHTML(alert.player_username || 'Unknown')} (${escapeHTML(alert.player_id)})</p>
        <p>${escapeHTML(alert.description || 'No details provided.')}</p>
        <p>${new Date(alert.created_at).toLocaleString()}</p>
        <button onclick="showAlertDetails('${escapeHTML(alert.id)}')">Details</button>`;
      container.appendChild(item);
    });
  } catch (err) {
    console.error('⚠️ Failed to load account alerts:', err);
    container.innerHTML = '<p class="error-msg">Failed to fetch alerts.</p>';
  }
}

// ✅ Admin Actions
window.flagUser = async userId => handleAdminAction('/api/admin/flag', { player_id: userId }, 'User flagged');
window.freezeUser = async userId => handleAdminAction('/api/admin/freeze', { player_id: userId }, 'User frozen');
window.banUser = async userId => handleAdminAction('/api/admin/ban', { player_id: userId }, 'User banned');
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
  await handleAdminAction('/api/admin/flags/toggle', { flag_key: key, value: val }, 'Flag updated');
}

async function updateKingdom() {
  const kid = document.getElementById('kingdom-id')?.value;
  const field = document.getElementById('kingdom-field')?.value;
  const value = document.getElementById('kingdom-value')?.value;
  if (!kid || !field) return alert('Missing field/kingdom');
  await handleAdminAction('/api/admin/kingdoms/update', {
    kingdom_id: Number(kid),
    field,
    value
  }, 'Kingdom updated');
}

async function forceEndWar() {
  const wid = document.getElementById('war-id')?.value;
  if (!wid) return alert('Enter war ID');
  await handleAdminAction('/api/admin/wars/force_end', { war_id: Number(wid) }, 'War ended');
}

async function rollbackCombatTick() {
  const wid = document.getElementById('war-id')?.value;
  if (!wid) return alert('Enter war ID');
  await handleAdminAction('/api/admin/wars/rollback_tick', { war_id: Number(wid) }, 'Tick rolled back');
}

async function rollbackDatabase() {
  const pass = document.getElementById('rollback-password')?.value;
  if (!pass) return alert('Enter master password');
  await handleAdminAction('/api/admin/rollback/database', { password: pass }, 'Rollback triggered');
}

// 🧩 Initialize DOM Hooks
document.addEventListener('DOMContentLoaded', () => {
  loadDashboardStats();
  loadPlayerList();
  loadAccountAlerts();
  loadFlaggedUsers();

  setInterval(() => {
    loadDashboardStats();
    loadFlaggedUsers();
  }, REFRESH_MS);

  supabase.channel('admin_dashboard_alerts')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'account_alerts' }, async () => {
      await loadAccountAlerts();
      await loadFlaggedUsers();
    }).subscribe();

  document.getElementById('search-btn')?.addEventListener('click', loadPlayerList);
  document.getElementById('status-filter')?.addEventListener('change', loadPlayerList);
  document.getElementById('load-logs-btn')?.addEventListener('click', loadAuditLogs);
  document.getElementById('toggle-flag-btn')?.addEventListener('click', toggleFlag);
  document.getElementById('update-kingdom-btn')?.addEventListener('click', updateKingdom);
  document.getElementById('force-end-war-btn')?.addEventListener('click', forceEndWar);
  document.getElementById('rollback-tick-btn')?.addEventListener('click', rollbackCombatTick);
  document.getElementById('rollback-btn')?.addEventListener('click', rollbackDatabase);
});
