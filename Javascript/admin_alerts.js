// Project Name: Thronestead©
// File Name: admin_alerts.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';

const REFRESH_MS = 30000;
let realtimeSub;

// ✅ Initialize alert loading and realtime subscription
document.addEventListener('DOMContentLoaded', () => {
  loadAlerts();
  setInterval(loadAlerts, REFRESH_MS);

  realtimeSub = supabase
    .channel('admin_alerts')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'admin_alerts' }, loadAlerts)
    .subscribe();

  document.getElementById('refresh-alerts')?.addEventListener('click', loadAlerts);
  document.getElementById('clear-filters')?.addEventListener('click', clearFilters);
});

// ✅ Cleanup on page unload
window.addEventListener('beforeunload', () => {
  realtimeSub?.unsubscribe();
});

// ✅ Load and render all alert categories
async function loadAlerts() {
  const container = document.getElementById('alerts-feed');
  if (!container) return;
  container.innerHTML = '<p>Loading alerts...</p>';

  try {
    const res = await fetch('/api/admin/alerts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(getFilters())
    });
    const data = await res.json();

    container.innerHTML = '';
    if (Array.isArray(data.alerts)) {
      data.alerts.forEach(alert => renderAlertCard(container, alert));
      bindNewActionHandlers();
    } else {
      renderCategory(container, 'Moderation', data.moderation_notes);
      renderCategory(container, 'War', data.recent_war_logs);
      renderCategory(container, 'Diplomacy', data.treaty_activity);
      renderCategory(container, 'Audit Log', data.audit);
      renderCategory(container, 'Admin Actions', data.admin_actions);
      attachActionHandlers();
    }
  } catch (err) {
    console.error('❌ Failed to load alerts:', err);
    container.innerHTML = '<p>Error loading alerts. Please try again later.</p>';
  }
}

// ✅ Handle action buttons like flag/freeze/ban/dismiss
function attachActionHandlers() {
  document.querySelectorAll('.action-buttons .action-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const { action, id: alertId, player: playerId } = btn.dataset;
      try {
        switch (action) {
          case 'flag': await flagPlayer(playerId, alertId); break;
          case 'freeze': await freezePlayer(playerId, alertId); break;
          case 'ban': await banPlayer(playerId, alertId); break;
          case 'dismiss': await dismissAlert(alertId); break;
        }
        await loadAlerts(); // reload after action
      } catch (err) {
        console.error(`❌ Action failed [${action}] for alert ${alertId}:`, err);
        alert(`❌ Action failed: ${err.message}`);
      }
    });
  });
}

// ✅ Action API endpoints
async function flagPlayer(playerId, alertId) {
  await postAdminAction('/api/admin/flag', { player_id: playerId, alert_id: alertId });
  alert('✅ Player flagged.');
}

async function freezePlayer(playerId, alertId) {
  await postAdminAction('/api/admin/freeze', { player_id: playerId, alert_id: alertId });
  alert('✅ Player frozen.');
}

async function banPlayer(playerId, alertId) {
  await postAdminAction('/api/admin/ban', { player_id: playerId, alert_id: alertId });
  alert('✅ Player banned.');
}

async function dismissAlert(alertId) {
  const { error } = await supabase.from('admin_alerts').delete().eq('id', alertId);
  if (error) throw new Error('Dismiss failed: ' + error.message);
  alert('✅ Alert dismissed.');
}

// ✅ Utility to send admin actions to API
async function postAdminAction(endpoint, payload) {
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Server error: ${errorText}`);
  }
}

// =====================
// 🔧 UI & Utility
// =====================

function getFilters() {
  const fields = ['start', 'end', 'type', 'severity', 'kingdom', 'alliance'];
  return Object.fromEntries(fields.map(f => [f, document.getElementById(`filter-${f}`)?.value]).filter(([, v]) => v));
}

function clearFilters() {
  document.querySelectorAll('.filter-input').forEach(el => (el.value = ''));
  loadAlerts();
}

// ✅ Render alert section
function renderCategory(container, title, items) {
  if (!items || items.length === 0) return;

  const section = document.createElement('div');
  section.className = 'alert-category';

  const header = document.createElement('h3');
  header.textContent = title;
  section.appendChild(header);

  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'alert-item ' + mapSeverity(item.severity || item.priority);
    div.textContent = formatItem(item);

    if (item.alert_id || item.player_id) {
      const actions = document.createElement('div');
      actions.className = 'action-buttons';
      ['flag', 'freeze', 'ban', 'dismiss'].forEach(action => {
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.textContent = action.charAt(0).toUpperCase() + action.slice(1);
        btn.dataset.action = action;
        btn.dataset.id = item.alert_id || item.id;
        btn.dataset.player = item.player_id;
        actions.appendChild(btn);
      });
      div.appendChild(actions);
    }

    section.appendChild(div);
  });

  container.appendChild(section);
}

// ✅ Severity → CSS mapping
function mapSeverity(sev) {
  const s = String(sev || '').toLowerCase();
  if (s.includes('high') || s.includes('critical')) return 'severity-high';
  if (s.includes('medium')) return 'severity-medium';
  return 'severity-low';
}

// ✅ Format alert item for display
function formatItem(item) {
  if (item.message) return `[${item.event_type || 'log'}] ${item.message}`;
  if (item.action && item.details) return `${item.action} - ${item.details}`;
  if (item.note) return item.note;
  return JSON.stringify(item);
}

// =====================
// 🆕 Simple card renderer
// =====================
function renderAlertCard(container, alert) {
  const el = document.createElement('div');
  el.className = `alert-card ${alert.severity || 'low'}`;
  el.innerHTML = `
    <strong>[${(alert.type || '').toUpperCase()}]</strong>
    <p>${alert.message || ''}</p>
    <span>Kingdom: ${alert.kingdom_id || '—'} | Alliance: ${alert.alliance_id || '—'} | ${new Date(alert.timestamp).toLocaleString()}</span>
  `;
  const actions = document.createElement('div');
  actions.className = 'alert-actions';
  actions.innerHTML = `
    <button class="btn btn-small flag-ip" data-ip="${alert.ip || ''}">Flag IP</button>
    <button class="btn btn-small suspend-account" data-uid="${alert.user_id || ''}">Suspend</button>
    <button class="btn btn-small mark-reviewed" data-id="${alert.alert_id}">Mark Reviewed</button>
  `;
  el.appendChild(actions);
  container.appendChild(el);
}

function bindNewActionHandlers() {
  document.querySelectorAll('.flag-ip').forEach(btn => {
    btn.addEventListener('click', async () => {
      await postAdminAction('/api/admin/flag_ip', { ip: btn.dataset.ip });
      alert('✅ IP flagged.');
    });
  });
  document.querySelectorAll('.suspend-account').forEach(btn => {
    btn.addEventListener('click', async () => {
      await postAdminAction('/api/admin/suspend_user', { user_id: btn.dataset.uid });
      alert('✅ Account suspended.');
    });
  });
  document.querySelectorAll('.mark-reviewed').forEach(btn => {
    btn.addEventListener('click', async () => {
      await postAdminAction('/api/admin/mark_alert_handled', { alert_id: btn.dataset.id });
      btn.disabled = true;
    });
  });
}
