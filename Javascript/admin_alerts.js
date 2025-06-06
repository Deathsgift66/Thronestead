/*
Project Name: Kingmakers Rise Frontend
File Name: admin_alerts.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ✅ On page load
document.addEventListener('DOMContentLoaded', () => {
  loadAlerts();

  // Refresh button
  document.getElementById('refresh-alerts').addEventListener('click', loadAlerts);

  // Clear filters
  document.getElementById('clear-filters').addEventListener('click', () => {
    document.getElementById('filter-username').value = '';
    document.getElementById('filter-type').value = '';
    document.getElementById('filter-date').value = '';
    loadAlerts();
  });
});

// ✅ Load alerts from database
async function loadAlerts() {
  const container = document.getElementById('alerts-container');
  container.innerHTML = '<p>Loading alerts...</p>';

  try {
    // Build filter conditions
    const usernameFilter = document.getElementById('filter-username').value.trim().toLowerCase();
    const typeFilter = document.getElementById('filter-type').value;
    const dateFilter = document.getElementById('filter-date').value;

    let query = supabase
      .from('account_alerts')
      .select('*')
      .order('created_at', { ascending: false });

    // Fetch raw data first
    const { data, error } = await query;

    if (error) throw new Error('Error loading alerts: ' + error.message);

    let filteredData = data;

    // Apply filters (client-side for now — can optimize to server later)
    if (usernameFilter) {
      filteredData = filteredData.filter(alert =>
        (alert.player_username || '').toLowerCase().includes(usernameFilter)
      );
    }

    if (typeFilter) {
      filteredData = filteredData.filter(alert => alert.alert_type === typeFilter);
    }

    if (dateFilter) {
      filteredData = filteredData.filter(alert => alert.created_at.startsWith(dateFilter));
    }

    // Render
    if (filteredData.length === 0) {
      container.innerHTML = '<p>No matching alerts found.</p>';
      return;
    }

    const table = document.createElement('table');
    table.innerHTML = `
      <thead>
        <tr>
          <th>Time</th>
          <th>Player</th>
          <th>Type</th>
          <th>Description</th>
          <th>Actions</th>
        </tr>
      </thead>`;

    const tbody = document.createElement('tbody');

    filteredData.forEach(alert => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${new Date(alert.created_at).toLocaleString()}</td>
        <td>${alert.player_username || 'Unknown'} (ID: ${alert.player_id})</td>
        <td>${alert.alert_type}</td>
        <td>${alert.description || '—'}</td>
        <td class="action-buttons">
          <button class="action-btn flag-btn" data-action="flag" data-id="${alert.id}" data-player="${alert.player_id}">Flag</button>
          <button class="action-btn freeze-btn" data-action="freeze" data-id="${alert.id}" data-player="${alert.player_id}">Freeze</button>
          <button class="action-btn ban-btn" data-action="ban" data-id="${alert.id}" data-player="${alert.player_id}">Ban</button>
          <button class="action-btn dismiss-btn" data-action="dismiss" data-id="${alert.id}">Dismiss</button>
        </td>`;
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.innerHTML = ''; // Clear loading text
    container.appendChild(table);

    attachActionHandlers();

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
  console.log(`🚩 Flagging player ${playerId} via alert ${alertId}`);
  await postAdminAction('/api/admin/flag', { player_id: playerId, alert_id: alertId });
  alert('✅ Player flagged.');
}

async function freezePlayer(playerId, alertId) {
  console.log(`❄️ Freezing player ${playerId} via alert ${alertId}`);
  await postAdminAction('/api/admin/freeze', { player_id: playerId, alert_id: alertId });
  alert('✅ Player frozen.');
}

async function banPlayer(playerId, alertId) {
  console.log(`🚫 Banning player ${playerId} via alert ${alertId}`);
  await postAdminAction('/api/admin/ban', { player_id: playerId, alert_id: alertId });
  alert('✅ Player banned.');
}

async function dismissAlert(alertId) {
  console.log(`🗑️ Dismissing alert ${alertId}`);
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
