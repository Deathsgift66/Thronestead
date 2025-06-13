/*
Project Name: Kingmakers Rise Frontend
File Name: admin_alerts.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

const REFRESH_MS = 30000;


// ✅ On page load
let realtimeSub;
document.addEventListener('DOMContentLoaded', () => {
  loadAlerts();
  setInterval(async () => { await loadAlerts(); }, REFRESH_MS);

  realtimeSub = supabase
    .channel('admin_alerts')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'account_alerts' }, async () => {
      await loadAlerts();
    })
    .subscribe();

  document.getElementById('refresh-alerts').addEventListener('click', loadAlerts);
  document.getElementById('clear-filters').addEventListener('click', clearFilters);
});

window.addEventListener('beforeunload', () => {
  realtimeSub?.unsubscribe();
});

// ✅ Load alerts from database
async function loadAlerts() {
  const container = document.getElementById('alerts-feed');
  container.innerHTML = '<p>Loading alerts...</p>';

  try {
    const params = new URLSearchParams(getFilters());
    const res = await fetch(`/api/admin/alerts?${params.toString()}`);
    const data = await res.json();

    container.innerHTML = '';
    renderCategory(container, 'Moderation', data.moderation_notes);
    renderCategory(container, 'War', data.recent_war_logs);
    renderCategory(container, 'Diplomacy', data.treaty_activity);
    renderCategory(container, 'Audit Log', data.audit);
    renderCategory(container, 'Admin Actions', data.admin_actions);
  } catch (err) {
    console.error('❌ Failed to load alerts:', err);
    container.innerHTML = '<p>Error loading alerts. Please try again later.</p>';
  }
}

// ✅ Attach handlers for action buttons
function attachActionHandlers() {
  document.querySelectorAll('.action-buttons .action-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      const action = btn.dataset.action;
      const alertId = btn.dataset.id;
      const playerId = btn.dataset.player;

      try {
        switch (action) {
          case 'flag': await flagPlayer(playerId, alertId); break;
          case 'freeze': await freezePlayer(playerId, alertId); break;
          case 'ban': await banPlayer(playerId, alertId); break;
          case 'dismiss': await dismissAlert(alertId); break;
        }

        // After action, reload
        await loadAlerts();
      } catch (err) {
        console.error(`❌ Action failed [${action}] for alert ${alertId}:`, err);
        alert(`❌ Action failed: ${err.message}`);
      }
    });
  });
}

// ✅ Action handlers (production-ready)
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
  const { error } = await supabase.from('account_alerts').delete().eq('id', alertId);
  if (error) throw new Error('Dismiss failed: ' + error.message);
  alert('✅ Alert dismissed.');
}

// ✅ Helper to post to admin API endpoints
async function postAdminAction(endpoint, payload) {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Server error: ${errText}`);
  }
}

// =====================
// Utility Functions
// =====================
function getFilters() {
  const entries = [
    ['start', document.getElementById('filter-start').value],
    ['end', document.getElementById('filter-end').value],
    ['type', document.getElementById('filter-alert-type').value],
    ['severity', document.getElementById('filter-severity').value],
    ['kingdom', document.getElementById('filter-kingdom').value],
    ['alliance', document.getElementById('filter-alliance').value],
  ];
  return Object.fromEntries(entries.filter(([, v]) => v));
}

function clearFilters() {
  document.querySelectorAll('.filter-input').forEach(el => (el.value = ''));
  loadAlerts();
}

function renderCategory(container, title, items) {
  if (!items || items.length === 0) return;
  const section = document.createElement('div');
  section.className = 'alert-category';
  const h = document.createElement('h3');
  h.textContent = title;
  section.appendChild(h);

  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'alert-item ' + mapSeverity(item.severity || item.priority);
    div.textContent = formatItem(item);
    section.appendChild(div);
  });

  container.appendChild(section);
}

function mapSeverity(sev) {
  if (!sev) return 'severity-low';
  const s = String(sev).toLowerCase();
  if (s.includes('high') || s.includes('critical')) return 'severity-high';
  if (s.includes('medium')) return 'severity-medium';
  return 'severity-low';
}

function formatItem(item) {
  if (item.message) return `[${item.event_type || 'log'}] ${item.message}`;
  if (item.action && item.details) return `${item.action} - ${item.details}`;
  if (item.note) return item.note;
  return JSON.stringify(item);
}
