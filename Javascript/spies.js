import { supabase } from './supabaseClient.js';

let currentUserId = null;
let realtimeChannel = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  currentUserId = session.user.id;

  const trainBtn = document.getElementById('train-btn');
  if (trainBtn) trainBtn.addEventListener('click', trainSpies);

  await loadSpies();
  await loadMissions();
  subscribeRealtime();
});

async function loadSpies() {
  const infoEl = document.getElementById('spy-info');
  infoEl.textContent = 'Loading...';
  try {
    const res = await fetch('/api/kingdom/spies', {
      headers: { 'X-User-ID': currentUserId }
    });
    const data = await res.json();
    infoEl.innerHTML = `
      <div>Spy Level: ${data.spy_level}</div>
      <div>Spies: ${data.spy_count} / ${data.max_spy_capacity}</div>
      <div>Progress XP: ${data.spy_xp}</div>
      <div>Upkeep: ${data.spy_upkeep_gold} gold/tick</div>
      <div>Spies Lost: ${data.spies_lost}</div>
      <div>Missions Attempted: ${data.missions_attempted}</div>
      <div>Successful Missions: ${data.missions_successful}</div>
    `;
  } catch (e) {
    infoEl.textContent = 'Failed to load spy info';
  }
}

async function loadMissions() {
  const listEl = document.getElementById('missions');
  listEl.textContent = 'Loading missions...';
  try {
    const res = await fetch('/api/kingdom/spy_missions', {
      headers: { 'X-User-ID': currentUserId }
    });
    const data = await res.json();
    listEl.innerHTML = '';
    (data.missions || []).forEach(m => {
      const div = document.createElement('div');
      const type = m.mission_type || m.mission;
      div.textContent = `${type} targeting ${m.target_id} - ${m.status}`;
      listEl.appendChild(div);
    });
  } catch (e) {
    listEl.textContent = 'Failed to load missions';
  }
}

async function trainSpies() {
  const qty = parseInt(document.getElementById('train-qty').value, 10);
  if (!qty) return;
  const res = await fetch('/api/kingdom/spies/train', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': currentUserId
    },
    body: JSON.stringify({ quantity: qty })
  });
  if (res.ok) {
    document.getElementById('train-qty').value = '';
    await loadSpies();
  }
}

function subscribeRealtime() {
  realtimeChannel = supabase
    .channel('spies-' + currentUserId)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'spy_missions', filter: `kingdom_id=eq.${currentUserId}` }, async () => {
      await loadMissions();
    })
    .on('postgres_changes', { event: '*', schema: 'public', table: 'kingdom_spies', filter: `kingdom_id=eq.${currentUserId}` }, async () => {
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

  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}
