// Project Name: Thronestead©
// File Name: battle_resolution.js
// Version:  7/21/2025 12:30
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';

let accessToken = null;
let userId = null;

// ===============================
// DOM READY
// ===============================

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  accessToken = session.access_token;
  userId = session.user.id;

  const warId = getWarIdFromURL();
  if (warId === null) {
    return;
  }
  await fetchBattleResolution(warId);

  document.getElementById('refresh-btn').addEventListener('click', () => {
    const id = getWarIdFromURL();
    if (id !== null) {
      fetchBattleResolution(id);
    }
  });
  document.getElementById('view-replay-btn').addEventListener('click', () => {
    const id = getWarIdFromURL();
    if (id !== null) {
      window.location.href = `/battle_replay.html?war_id=${id}`;
    }
  });
  setInterval(() => {
    const id = getWarIdFromURL();
    if (id !== null) {
      fetchBattleResolution(id);
    }
  }, 30000);

  // log to audit_log (best effort)
  try {
    await supabase.from('audit_log').insert({
      user_id: session.user.id,
      action: 'view_battle_resolution',
      details: `War ${warId}`
    });
  } catch {
    console.warn('audit log insert failed');
  }
});

// ===============================
// LOAD RESOLUTION DATA
// ===============================
async function fetchBattleResolution(warId) {
  document.getElementById('resolution-summary').innerHTML = '<p>Loading results...</p>';
  const res = await fetch(`/api/battle/resolution?war_id=${warId}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'X-User-ID': userId
    }
  });
  if (!res.ok) {
    document.getElementById('resolution-summary').textContent = '❌ Failed to load battle results.';
    return;
  }
  const data = await res.json();
  renderResolutionData(data);
  document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
}

function renderResolutionData(data) {
  const summary = document.getElementById('resolution-summary');
  const scoreBox = document.getElementById('score-breakdown');
  const timeline = document.getElementById('combat-timeline');
  const casualty = document.getElementById('casualty-report');
  const lootBox = document.getElementById('loot-summary');
  const participantsBox = document.getElementById('participant-breakdown');
  const statBox = document.getElementById('stat-changes');

  summary.innerHTML = `
    <h3>Victory: ${data.winner}</h3>
    <p>Battle Duration: ${data.duration_ticks} ticks</p>
    <p>Victor Score: ${data.victor_score}</p>
  `;

  casualty.innerHTML = renderCasualties(data.casualties);
  lootBox.innerHTML = renderLoot(data.loot);

  if (data.score_breakdown) {
    scoreBox.innerHTML = `<pre>${JSON.stringify(data.score_breakdown, null, 2)}</pre>`;
  }

  if (Array.isArray(data.timeline)) {
    const list = document.createElement('ul');
    data.timeline.forEach(t => {
      const li = document.createElement('li');
      li.className = 'combat-log-entry';
      li.textContent = t;
      list.appendChild(li);
    });
    timeline.innerHTML = '';
    timeline.appendChild(list);
  }

  if (data.stat_changes) {
    const list = document.createElement('ul');
    for (const [k, v] of Object.entries(data.stat_changes)) {
      const li = document.createElement('li');
      li.textContent = `${k}: ${v}`;
      list.appendChild(li);
    }
    statBox.innerHTML = '';
    statBox.appendChild(list);
  }

  if (data.participants) {
    participantsBox.innerHTML = '';
    for (const [side, names] of Object.entries(data.participants)) {
      const div = document.createElement('div');
      div.className = 'participant-box';
      div.innerHTML = `<strong>${side}</strong>: ${names.join(', ')}`;
      participantsBox.appendChild(div);
    }
  }

  document.getElementById('replay-button').innerHTML =
    `<a href="battle_replay.html?war_id=${getWarIdFromURL()}" class="royal-button">Replay Battle</a>`;
}

function renderCasualties(c) {
  if (!c) return '';
  const div = document.createElement('div');
  div.innerHTML = '<h3>Casualties</h3>';
  for (const [side, obj] of Object.entries(c)) {
    const p = document.createElement('p');
    const count = Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ');
    p.textContent = `${side}: ${count}`;
    div.appendChild(p);
  }
  return div.innerHTML;
}

function renderLoot(loot) {
  if (!loot) return '';
  const div = document.createElement('div');
  div.innerHTML = '<h3>Loot</h3>';
  const ul = document.createElement('ul');
  for (const [res, amount] of Object.entries(loot)) {
    const li = document.createElement('li');
    li.textContent = `${res}: ${amount}`;
    ul.appendChild(li);
  }
  div.appendChild(ul);
  return div.innerHTML;
}

function getWarIdFromURL() {
  const params = new URLSearchParams(window.location.search);
  const warId = parseInt(params.get('war_id'), 10);
  if (isNaN(warId)) {
    alert('⚠ Invalid war ID');
    return null;
  }
  return warId;
}

