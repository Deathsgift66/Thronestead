// Project Name: Thronestead©
// File Name: admin_alerts.js
// Version: 7/18/2025
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { authFetch, authJsonFetch, showToast, formatTimestamp } from './core_utils.js';
import { setupReauthButtons } from './reauth.js';

const REFRESH_INTERVAL_MS = 30000;
let realtimeSub = null;

export function init() {
  setupReauthButtons('.action-btn');
  document.getElementById('refresh-alerts')?.addEventListener('click', loadAlerts);
  document.getElementById('clear-filters')?.addEventListener('click', clearFilters);

  loadAlerts();
  subscribeToRealtime();
  setInterval(loadAlerts, REFRESH_INTERVAL_MS);

  window.addEventListener('beforeunload', () => {
    if (realtimeSub?.unsubscribe) realtimeSub.unsubscribe();
  });
}

function subscribeToRealtime() {
  realtimeSub = supabase
    .channel('admin_alerts')
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'admin_alerts'
    }, loadAlerts)
    .subscribe();
}

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

function renderCategory(container, title, items = []) {
  if (!Array.isArray(items) || !items.length) return;

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
      <small>Kingdom: ${item.kingdom_id || '—'} | Alliance: ${item.alliance_id || '—'} | ${formatTimestamp(item.timestamp)}</small>
    `;

    const actions = document.createElement('div');
    actions.className = 'action-buttons';
    getActions(item).forEach(({ label, action, data }) => {
      const btn = document.createElement('button');
      btn.className = 'btn btn-small action-btn';
      btn.textContent = label;
      btn.dataset.action = action;
      Object.entries(data).forEach(([k, v]) => btn.dataset[k] = v);
      actions.appendChild(btn);
    });

    div.appendChild(actions);
    section.appendChild(div);
  });

  container.appendChild(section);
}

function getActions(item) {
  const map = [
    { action: 'flag', label: 'Flag', data: { player_id: item.player_id } },
    { action: 'freeze', label: 'Freeze', data: { player_id: item.player_id } },
    { action: 'ban', label: 'Ban', data: { player_id: item.player_id } },
    { action: 'dismiss', label: 'Dismiss', data: { alert_id: item.alert_id || item.id } },
    { action: 'flag_ip', label: 'Flag IP', data: { ip: item.ip } },
    { action: 'suspend_user', label: 'Suspend', data: { user_id: item.user_id } },
    { action: 'mark_alert_handled', label: 'Mark Reviewed', data: { alert_id: item.alert_id || item.id } }
  ];

  return map.filter(({ data }) => Object.values(data).some(Boolean));
}

document.addEventListener('click', async e => {
  if (!e.target.matches('.action-btn')) return;
  const btn = e.target;
  const action = btn.dataset.action;

  try {
    switch (action) {
      case 'flag':
      case 'freeze':
      case 'ban':
        await postAdminAction(`/api/admin/${action}`, {
          player_id: btn.dataset.player_id,
          alert_id: btn.dataset.alert_id
        });
        break;

      case 'dismiss':
        await supabase.from('admin_alerts')
          .delete()
          .eq('alert_id', btn.dataset.alert_id);
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

    showToast(`✅ ${action.replace(/_/g, ' ')} successful.`, 'success');
    loadAlerts();
  } catch (err) {
    console.error(`❌ Action [${action}] failed:`, err);
    showToast(`❌ ${action} failed: ${err.message}`, 'error');
  }
});

async function postAdminAction(endpoint, payload) {
  const res = await authFetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
}

function getFilters() {
  return Object.fromEntries(
    ['start', 'end', 'type', 'severity', 'kingdom', 'alliance']
      .map(key => {
        const el = document.getElementById(`filter-${key}`);
        return [key, el?.value?.trim()];
      })
      .filter(([, val]) => val)
  );
}

function clearFilters() {
  document.querySelectorAll('.filter-input').forEach(el => (el.value = ''));
  loadAlerts();
}

function mapSeverity(sev = '') {
  const s = String(sev).toLowerCase();
  if (s.includes('critical') || s.includes('high')) return 'severity-high';
  if (s.includes('medium')) return 'severity-medium';
  return 'severity-low';
}

function formatItem(item = {}) {
  return item.message || `${item.action || ''} - ${item.details || item.note || JSON.stringify(item)}`;
}


