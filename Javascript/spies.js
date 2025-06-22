// Project Name: Thronestead©
// File Name: spies.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

let currentUserId = null;
let currentSession = null;
let realtimeChannel = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  currentUserId = session.user.id;
  currentSession = session;

  const trainBtn = document.getElementById('train-btn');
  if (trainBtn) trainBtn.addEventListener('click', trainSpies);

  await loadSpies();
  await loadMissions();
  subscribeRealtime();
});

/**
 * Load current spy stats for the player's kingdom
 */
async function loadSpies() {
  const infoEl = document.getElementById('spy-info');
  infoEl.textContent = 'Loading...';
  try {
    const res = await fetch('https://thronestead.onrender.com/api/kingdom/spies', {
      headers: {
        'X-User-ID': currentUserId,
        Authorization: `Bearer ${currentSession.access_token}`
      }
    });
    if (!res.ok) throw new Error('Failed to fetch spies');
    const data = await res.json();

    infoEl.innerHTML = `
      <div>🕵️ Spy Level: ${data.spy_level}</div>
      <div>🧍 Spies: ${data.spy_count} / ${data.max_spy_capacity}</div>
      <div>💸 Upkeep: ${data.spy_upkeep_gold} gold/tick</div>
      <div>💀 Spies Lost: ${data.spies_lost}</div>
      <div>🎯 Missions Attempted: ${data.missions_attempted}</div>
      <div>✅ Successful Missions: ${data.missions_successful}</div>
    `;
  } catch (err) {
    console.error('loadSpies error:', err);
    infoEl.textContent = 'Failed to load spy info';
    showToast('Could not load spy stats.');
  }
}

/**
 * Load all spy missions (active, failed, complete)
 */
async function loadMissions() {
  const listEl = document.getElementById('missions');
  listEl.textContent = 'Loading missions...';
  try {
    const res = await fetch('https://thronestead.onrender.com/api/kingdom/spy_missions', {
      headers: {
        'X-User-ID': currentUserId,
        Authorization: `Bearer ${currentSession.access_token}`
      }
    });
    if (!res.ok) throw new Error('Failed to fetch missions');
    const data = await res.json();

    listEl.innerHTML = '';
    if (!data.missions?.length) {
      listEl.innerHTML = '<p>No active missions.</p>';
      return;
    }

    data.missions.forEach(m => {
      const div = document.createElement('div');
      const type = m.mission_type || m.mission || 'Unknown';
      const status = m.status || 'Pending';

      div.className = `mission-card status-${status.toLowerCase()}`;
      div.innerHTML = `
        <strong>${type}</strong> targeting <em>${m.target_id}</em><br/>
        <span>Status:</span> ${status}
      `;
      listEl.appendChild(div);
    });
  } catch (err) {
    console.error('loadMissions error:', err);
    listEl.textContent = 'Failed to load missions';
    showToast('Could not load missions.');
  }
}

/**
 * Send a POST request to train spies
 */
async function trainSpies() {
  const qtyEl = document.getElementById('train-qty');
  const qty = parseInt(qtyEl.value, 10);
  if (!qty || qty < 1) {
    showToast('Enter a valid number of spies to train.');
    return;
  }

  try {
    const res = await fetch('https://thronestead.onrender.com/api/kingdom/spies/train', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': currentUserId,
        Authorization: `Bearer ${currentSession.access_token}`
      },
      body: JSON.stringify({ quantity: qty })
    });

    const result = await res.json();

    if (!res.ok) throw new Error(result.error || 'Training failed');

    showToast(result.message || 'Spies training initiated.');
    qtyEl.value = '';
    await loadSpies();
  } catch (err) {
    console.error('trainSpies error:', err);
    showToast('Failed to train spies.');
  }
}

/**
 * Subscribe to realtime updates via Supabase
 */
function subscribeRealtime() {
  if (!currentUserId) return;

  realtimeChannel = supabase
    .channel('spies-' + currentUserId)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'spy_missions',
      filter: `kingdom_id=eq.${currentUserId}`
    }, async () => {
      await loadMissions();
    })
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'kingdom_spies',
      filter: `kingdom_id=eq.${currentUserId}`
    }, async () => {
      await loadSpies();
    })
    .subscribe(status => {
      const indicator = document.getElementById('realtime-indicator');
      if (indicator) {
        if (status === 'SUBSCRIBED') {
          indicator.textContent = 'Live';
          indicator.className = 'connected';
        } else {
          indicator.textContent = 'Offline';
          indicator.className = 'disconnected';
        }
      }
    });

  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) {
      supabase.removeChannel(realtimeChannel);
    }
  });
}

/**
 * Show user feedback via on-screen toast
 */
function showToast(msg) {
  const toastEl = document.getElementById('toast');
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add('show');

  setTimeout(() => {
    toastEl.classList.remove('show');
  }, 3000);
}
