// Comment
// Project Name: Thronestead©
// File Name: admin_alerts.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { authFetch, authJsonFetch } from './utils.js';
import { setupReauthButtons } from './reauth.js';

const REFRESH_MS = 30000;
let realtimeSub = null;

// ✅ Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadAlerts();
  setInterval(loadAlerts, REFRESH_MS);
  subscribeToRealtime();
  document.getElementById('refresh-alerts')?.addEventListener('click', loadAlerts);
  document.getElementById('clear-filters')?.addEventListener('click', clearFilters);
  setupReauthButtons('.action-btn');
});

window.addEventListener('beforeunload', () => {
  realtimeSub?.unsubscribe();
});

// ✅ Realtime Sub
function subscribeToRealtime() {
  realtimeSub = supabase
    .channel('admin_alerts')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'admin_alerts' }, loadAlerts)
    .subscribe();
}

// ✅ Load alerts
async function loadAlerts() {
  const container = document.getElementById('alerts-feed');
  if (!container) return;
  container.innerHTML = '<p>Loading alerts...</p>';

  try {
    const data = await authJsonFetch('/api/admin/alerts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(getFilters())
    });

    container.innerHTML = '';

    const renderSet = Array.isArray(data.alerts)
      ? [{ title: 'Alerts', items: data.alerts }]
      : [
          { title: 'Moderation', items: data.moderation_notes },
          { title: 'War', items: data.recent_war_logs },
          { title: 'Diplomacy', items: data.treaty_activity },
          { title: 'Audit Log', items: data.audit },
          { title: 'Admin Actions', items: data.admin_actions }
        ];

    renderSet.forEach(({ title, items }) => renderCategory(container, title, items));
  } catch (err) {
    console.error('❌ Failed to load alerts:', err);
    container.innerHTML = '<p>Error loading alerts. Please try again later.</p>';
  }
}

// ✅ Render category + items
function renderCategory(container, title, items = []) {
  if (!items.length) return;

  const section = document.createElement('div');
  section.className = 'alert-category';

  const header = document.createElement('h3');
  header.textContent = title;
  section.appendChild(header);

  items.forEach(item => {
    const div = document.createElement('div');
    div.className = `alert-item ${mapSeverity(item.severity || item.priority)}`;
    div.innerHTML = `
      <strong>[${(item.event_type || item.type || 'log').toUpperCase()}]</strong>
      <p>${formatItem(item)}</p>
      <small>Kingdom: ${item.kingdom_id || '—'} | Alliance: ${item.alliance_id || '—'} | ${formatTime(item.timestamp)}</small>
    `;

    const actions = document.createElement('div');
    actions.className = 'action-buttons';
    const actionMap = [
      { action: 'flag', label: 'Flag', data: { player_id: item.player_id } },
      { action: 'freeze', label: 'Freeze', data: { player_id: item.player_id } },
      { action: 'ban', label: 'Ban', data: { player_id: item.player_id } },
      { action: 'dismiss', label: 'Dismiss', data: { alert_id: item.alert_id || item.id } },
      { action: 'flag_ip', label: 'Flag IP', data: { ip: item.ip } },
      { action: 'suspend_user', label: 'Suspend', data: { user_id: item.user_id } },
      { action: 'mark_alert_handled', label: 'Mark Reviewed', data: { alert_id: item.alert_id || item.id } }
    ];

    actionMap.forEach(({ action, label, data }) => {
      if (!Object.values(data).some(Boolean)) return;
      const btn = document.createElement('button');
      btn.className = 'btn btn-small action-btn';
      btn.textContent = label;
      btn.dataset.action = action;
      Object.entries(data).forEach(([k, v]) => (btn.dataset[k] = v));
      actions.appendChild(btn);
    });

    div.appendChild(actions);
    section.appendChild(div);
  });

  container.appendChild(section);
}

// ✅ Action dispatcher
document.addEventListener('click', async e => {
  if (!e.target.classList.contains('action-btn')) return;
  const btn = e.target;
  const action = btn.dataset.action;

  try {
    switch (action) {
      case 'flag':
        await postAdminAction('/api/admin/flag', { player_id: btn.dataset.player_id, alert_id: btn.dataset.alert_id });
        break;
      case 'freeze':
        await postAdminAction('/api/admin/freeze', { player_id: btn.dataset.player_id, alert_id: btn.dataset.alert_id });
        break;
      case 'ban':
        await postAdminAction('/api/admin/ban', { player_id: btn.dataset.player_id, alert_id: btn.dataset.alert_id });
        break;
      case 'dismiss':
        await supabase.from('admin_alerts').delete().eq('alert_id', btn.dataset.alert_id);
        break;
      case 'flag_ip':
        await postAdminAction('/api/admin/flag_ip', { ip: btn.dataset.ip });
        break;
      case 'suspend_user':
        await postAdminAction('/api/admin/suspend_user', { user_id: btn.dataset.user_id });
        break;
      case 'mark_alert_handled':
        await postAdminAction('/api/admin/mark_alert_handled', { alert_id: btn.dataset.alert_id });
        btn.disabled = true;
        break;
    }

    alert(`✅ ${action.replace(/_/g, ' ')} successful.`);
    loadAlerts();
  } catch (err) {
    console.error(`❌ Action [${action}] failed:`, err);
    alert(`❌ ${action} failed: ${err.message}`);
  }
});

// ✅ POST helper
async function postAdminAction(endpoint, payload) {
  const res = await authFetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
}

// ✅ Filter helpers
function getFilters() {
  return Object.fromEntries(
    ['start', 'end', 'type', 'severity', 'kingdom', 'alliance']
      .map(k => [k, document.getElementById(`filter-${k}`)?.value])
      .filter(([, v]) => v)
  );
}

function clearFilters() {
  document.querySelectorAll('.filter-input').forEach(el => (el.value = ''));
  loadAlerts();
}

// ✅ Misc formatting
function mapSeverity(sev = '') {
  const s = sev.toLowerCase();
  if (s.includes('high') || s.includes('critical')) return 'severity-high';
  if (s.includes('medium')) return 'severity-medium';
  return 'severity-low';
}

function formatItem(item) {
  return item.message || `${item.action || ''} - ${item.details || item.note || JSON.stringify(item)}`;
}

function formatTime(ts) {
  return ts ? new Date(ts).toLocaleString() : '';
}
