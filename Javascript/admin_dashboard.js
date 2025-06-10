/*
Project Name: Kingmakers Rise Frontend
File Name: admin_dashboard.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

const REFRESH_MS = 30000;


// 🟢 Load Game-Wide Dashboard Stats
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

// 🧑‍⚖️ Load Player List (with filters)
async function loadPlayerList() {
  const searchTerm = document.getElementById('search-player').value.toLowerCase();
  const statusFilter = document.getElementById('status-filter').value;
  const container = document.getElementById('player-list');
  container.innerHTML = '<p>Loading players...</p>';

  try {
    const { data: players, error } = await supabase.from('users').select('*');
    if (error) throw new Error('Failed to fetch players: ' + error.message);

    const filtered = players.filter(player => {
      const matchesName = player.username?.toLowerCase().includes(searchTerm);
      const matchesStatus = !statusFilter || player.status === statusFilter;
      return matchesName && matchesStatus;
    });

    container.innerHTML = '';
    if (filtered.length === 0) {
      container.innerHTML = '<p>No players found.</p>';
      return;
    }

    filtered.forEach(player => {
      const card = document.createElement('div');
      card.className = 'player-card';
      card.innerHTML = `
        <p><strong>${player.username}</strong> (${player.id})</p>
        <p>Status: ${player.status}</p>
        <div class="player-actions">
          <button onclick="flagUser('${player.id}')">Flag</button>
          <button onclick="freezeUser('${player.id}')">Freeze</button>
          <button onclick="banUser('${player.id}')">Ban</button>
        </div>`;
      container.appendChild(card);
    });


  } catch (err) {
    console.error('⚠️ Failed to load player list:', err);
    container.innerHTML = '<p class="error-msg">Failed to fetch players.</p>';
  }
}

// 📜 Load Audit Log History
async function loadAuditLogs() {
  const container = document.getElementById('log-list');
  container.innerHTML = '<p>Loading logs...</p>';

  try {
    const res = await fetch('/api/admin/audit/logs');
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    const logs = await res.json();

    container.innerHTML = '';
    if (logs.length === 0) {
      container.innerHTML = '<p>No audit logs found.</p>';
      return;
    }

    logs.forEach(log => {
      const entry = document.createElement('div');
      entry.className = 'log-card';
      entry.innerHTML = `
        <p><strong>${log.action}</strong> — ${log.details}</p>
        <p class="log-time">${new Date(log.created_at).toLocaleString()}</p>`;
      container.appendChild(entry);
    });


  } catch (err) {
    console.error('⚠️ Failed to load audit logs:', err);
    container.innerHTML = '<p class="error-msg">Failed to fetch audit logs.</p>';
  }
}

// 🚩 Load flagged users from the admin API
async function loadFlaggedUsers() {
  const container = document.getElementById('flagged-list');
  if (!container) return;
  container.innerHTML = '<p>Loading flagged players...</p>';

  try {
    const res = await fetch('/api/admin/flagged');
    if (!res.ok) throw new Error('Failed to fetch flagged users');
    const rows = await res.json();

    container.innerHTML = '';
    if (rows.length === 0) {
      container.innerHTML = '<p>No flagged users.</p>';
      return;
    }

    rows.forEach(row => {
      const card = document.createElement('div');
      card.className = 'flagged-card';
      card.innerHTML = `
        <p><strong>${row.player_id}</strong> — ${row.alert_type}</p>
        <p>${new Date(row.created_at).toLocaleString()}</p>`;
      container.appendChild(card);
    });
  } catch (err) {
    console.error('Failed to load flagged users:', err);
    container.innerHTML = '<p>Error loading flagged users.</p>';
  }
}

// 🚨 Load Recent Account Alerts
async function loadAccountAlerts() {
  const container = document.getElementById('alerts');
  container.innerHTML = '<p>Loading alerts...</p>';

  try {
    const { data: alerts, error } = await supabase
      .from('account_alerts')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw new Error('Failed to fetch alerts: ' + error.message);

    container.innerHTML = '';
    if (alerts.length === 0) {
      container.innerHTML = '<p>No alerts found.</p>';
      return;
    }

    alerts.forEach(alert => {
      const item = document.createElement('div');
      item.className = 'alert-item';
      item.innerHTML = `
        <p><strong>${alert.alert_type}</strong> — ${alert.player_username || 'Unknown'} (${alert.player_id})</p>
        <p>${alert.description || 'No details provided.'}</p>
        <p>${new Date(alert.created_at).toLocaleString()}</p>
        <button onclick="showAlertDetails('${alert.id}')">Details</button>`;
      container.appendChild(item);
    });


  } catch (err) {
    console.error('⚠️ Failed to load account alerts:', err);
    container.innerHTML = '<p class="error-msg">Failed to fetch alerts.</p>';
  }
}

// 🎯 Admin Action Functions
window.flagUser = async function (userId) {
  try {
    await postAdminAction('/api/admin/flag', { player_id: userId });
    alert('✅ User flagged.');
  } catch (err) {
    console.error('❌ Flag failed:', err);
    alert('❌ Flag failed: ' + err.message);
  }
};

window.freezeUser = async function (userId) {
  try {
    await postAdminAction('/api/admin/freeze', { player_id: userId });
    alert('✅ User frozen.');
  } catch (err) {
    console.error('❌ Freeze failed:', err);
    alert('❌ Freeze failed: ' + err.message);
  }
};

window.banUser = async function (userId) {
  try {
    await postAdminAction('/api/admin/ban', { player_id: userId });
    alert('✅ User banned.');
  } catch (err) {
    console.error('❌ Ban failed:', err);
    alert('❌ Ban failed: ' + err.message);
  }
};

window.showAlertDetails = function (alertId) {
  alert(`📋 Detailed view for Alert ID: ${alertId} will load here (future modal).`);
};

// Helper to POST to admin endpoints
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

// Toggle a system flag using the admin API
async function toggleFlag() {
  const key = document.getElementById('flag-key').value;
  const val = document.getElementById('flag-value').value === 'true';
  try {
    await postAdminAction('/api/admin/flags/toggle', { flag_key: key, value: val });
    alert('Flag updated');
  } catch (err) {
    console.error('Flag update failed:', err);
    alert('Failed to update flag');
  }
}

// Update a kingdom field via the admin API
async function updateKingdom() {
  const kid = document.getElementById('kingdom-id').value;
  const field = document.getElementById('kingdom-field').value;
  const value = document.getElementById('kingdom-value').value;
  try {
    await postAdminAction('/api/admin/kingdoms/update', {
      kingdom_id: Number(kid),
      field,
      value
    });
    alert('Kingdom updated');
  } catch (err) {
    console.error('Kingdom update failed:', err);
    alert('Failed to update kingdom');
  }
}
async function forceEndWar() {
  const wid = document.getElementById("war-id").value;
  if (!wid) return alert("Enter war ID");
  try {
    await postAdminAction("/api/admin/wars/force_end", { war_id: Number(wid) });
    alert("War ended");
  } catch (err) {
    console.error("Force end failed:", err);
    alert("Failed to end war");
  }
}

async function rollbackCombatTick() {
  const wid = document.getElementById("war-id").value;
  if (!wid) return alert("Enter war ID");
  try {
    await postAdminAction("/api/admin/wars/rollback_tick", { war_id: Number(wid) });
    alert("Tick rolled back");
  } catch (err) {
    console.error("Rollback failed:", err);
    alert("Failed to rollback tick");
  }
}


// 🧩 DOM Ready Hooks
document.addEventListener('DOMContentLoaded', () => {
  loadDashboardStats();
  loadPlayerList();
  loadAccountAlerts();
  loadFlaggedUsers();

  setInterval(() => {
    loadDashboardStats();
    loadFlaggedUsers();
  }, REFRESH_MS);

  supabase
    .channel('admin_dashboard_alerts')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'account_alerts' }, () => {
      loadAccountAlerts();
      loadFlaggedUsers();
    })
    .subscribe();

  document.getElementById('search-btn').addEventListener('click', loadPlayerList);
  document.getElementById('status-filter').addEventListener('change', loadPlayerList);
  document.getElementById('load-logs-btn').addEventListener('click', loadAuditLogs);
  document.getElementById('toggle-flag-btn').addEventListener('click', toggleFlag);
  document.getElementById('update-kingdom-btn').addEventListener('click', updateKingdom);
  document.getElementById("force-end-war-btn").addEventListener("click", forceEndWar);
  document.getElementById("rollback-tick-btn").addEventListener("click", rollbackCombatTick);
});
