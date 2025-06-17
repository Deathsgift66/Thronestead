// Project Name: Thronestead©
// File Name: alliance_wars.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { loadCustomBoard } from './customBoard.js';
import { escapeHTML } from './utils.js';
import { setupTabs } from './components/tabControl.js';

let currentWarId = null;
let combatInterval = null;
let switchTab = () => {};

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Logout binding
  document.getElementById("logout-btn")?.addEventListener("click", async () => {
    await supabase.auth.signOut();
    window.location.href = "index.html";
  });

  // ✅ Init
  switchTab = setupTabs({ onShow: id => id !== 'tab-live' && stopCombatPolling() });
  await loadCustomBoard({ altText: 'Alliance War Banner' });
  await loadAllianceWars();
  await loadPendingWars();

  document.getElementById('declare-alliance-war-btn')?.addEventListener('click', submitDeclareWar);
});


// ✅ Load All Active and Completed Wars
async function loadAllianceWars() {
  const container = document.getElementById("wars-container");
  container.innerHTML = "<p>Loading alliance wars...</p>";

  try {
    const [activeRes, fullRes] = await Promise.all([
      fetch('/api/alliance-wars/active'),
      fetch('/api/alliance-wars/list')
    ]);
    const activeWars = (await activeRes.json()).wars || [];
    const allWars = await fullRes.json();

    container.innerHTML = "";

    // Active
    if (activeWars.length > 0) {
      container.innerHTML += `<h3>⚔️ Active Wars</h3>`;
      activeWars.forEach(renderWarCard(container, true));
    } else {
      container.innerHTML += `<p>No active wars.</p>`;
    }

    // Completed
    if (allWars.completed_wars?.length > 0) {
      container.innerHTML += `<h3>🏅 Past Wars</h3>`;
      allWars.completed_wars.forEach(renderWarCard(container, false));
    }

    // View War Listeners
    document.querySelectorAll(".view-war-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const war = JSON.parse(btn.dataset.war);
        viewWarDetails(war);
      });
    });

  } catch (err) {
    console.error("❌ Error loading alliance wars:", err);
    container.innerHTML = "<p>Failed to load alliance wars.</p>";
  }
}

// ✅ Render War Card
function renderWarCard(container, isActive) {
  return war => {
    const card = document.createElement("div");
    card.className = "war-card";
    card.innerHTML = `
      <h4>${escapeHTML(war.opponent)}</h4>
      ${isActive
        ? `<p>Status: <strong>${escapeHTML(war.status)}</strong></p>
           <p>Turns Left: <strong>${escapeHTML(String(war.turns_left))}</strong></p>`
        : `<p>Result: <strong>${escapeHTML(war.result)}</strong></p>`}
      <p>Type: <strong>${escapeHTML(war.type)}</strong></p>
      <p>${isActive ? "Started" : "Ended"}: <strong>${escapeHTML(war.started || war.ended)}</strong></p>
      <div class="war-actions">
        <button class="action-btn view-war-btn" data-war='${JSON.stringify(war)}'>View</button>
      </div>`;
    container.appendChild(card);
  };
}

// ✅ View War Details → Loads battle map, overview, logs, participants
async function viewWarDetails(war) {
  currentWarId = war.alliance_war_id || war.id;
  switchTab('tab-overview');
  try {
    const res = await fetch(`/api/alliance-wars/view?alliance_war_id=${currentWarId}`);
    const { war: w, score, map } = await res.json();
    renderWarOverview(w, score);
    renderBattleMap(map?.tile_map || []);
    await loadCombatLogs();
    await loadScoreboard();
    await loadParticipants();
    startCombatPolling();
  } catch (err) {
    console.error("Error loading war details:", err);
  }
}

// ✅ Overview Details
function renderWarOverview(war, score) {
  const el = document.getElementById('war-overview');
  if (!war) return el.textContent = 'No data.';
  el.innerHTML = `
    <p><strong>Attacker:</strong> ${escapeHTML(war.attacker_alliance_id)}</p>
    <p><strong>Defender:</strong> ${escapeHTML(war.defender_alliance_id)}</p>
    <p><strong>Status:</strong> ${escapeHTML(war.war_status)}</p>
    <p><strong>Phase:</strong> ${escapeHTML(war.phase)}</p>
    <p><strong>Attacker Score:</strong> ${escapeHTML(String(score?.attacker_score ?? 0))}</p>
    <p><strong>Defender Score:</strong> ${escapeHTML(String(score?.defender_score ?? 0))}</p>
    <button id="join-war-btn" class="action-btn">Join War</button>
    <button id="surrender-btn" class="action-btn">Surrender</button>
  `;
  document.getElementById('join-war-btn').onclick = () => joinWar('attacker');
  document.getElementById('surrender-btn').onclick = surrenderWar;
}

// ✅ Grid Map
function renderBattleMap(tileMap) {
  const battleMap = document.getElementById('battle-map');
  battleMap.innerHTML = '';
  const height = tileMap.length;
  const width = tileMap[0]?.length || 60;
  battleMap.style.gridTemplateColumns = `repeat(${width}, 20px)`;
  tileMap.flat().forEach(type => {
    const tile = document.createElement('div');
    tile.className = 'tile';
    tile.style.backgroundColor = {
      forest: '#228B22', river: '#1E90FF', hill: '#8B4513'
    }[type] || '#ccc';
    battleMap.appendChild(tile);
  });
}

// ✅ Logs
async function loadCombatLogs() {
  if (!currentWarId) return;
  try {
    const res = await fetch(`/api/alliance-wars/combat-log?alliance_war_id=${currentWarId}`);
    const logs = (await res.json()).combat_logs || [];
    const logEl = document.getElementById('combat-log');
    logEl.innerHTML = '<strong>Combat Log:</strong><hr>' + logs.map(l =>
      `<div>[Tick ${l.tick_number}] ${l.event_type} — ${l.notes}</div>`).join('');
  } catch (err) {
    console.error("Combat log error:", err);
  }
}

// ✅ Score
async function loadScoreboard() {
  try {
    const res = await fetch(`/api/alliance-wars/scoreboard?alliance_war_id=${currentWarId}`);
    renderScoreboard(await res.json());
  } catch (err) {
    console.error("Scoreboard error:", err);
  }
}

function renderScoreboard(score) {
  document.getElementById('scoreboard').innerHTML = `
    <table class="score-table">
      <tr><th>Side</th><th>Score</th><th>Kills</th><th>Losses</th></tr>
      <tr><td>Attacker</td><td>${score.attacker_score}</td><td>${score.attacker_kills}</td><td>${score.attacker_losses}</td></tr>
      <tr><td>Defender</td><td>${score.defender_score}</td><td>${score.defender_kills}</td><td>${score.defender_losses}</td></tr>
      <tr><th colspan="2">Resources Plundered</th><td colspan="2">${score.resources_plundered}</td></tr>
      <tr><th colspan="2">Battles Participated</th><td colspan="2">${score.battles_participated}</td></tr>
    </table>`;
}

// ✅ Participants
async function loadParticipants() {
  const { data } = await supabase
    .from('alliance_war_participants')
    .select('kingdom_id, role')
    .eq('alliance_war_id', currentWarId);
  renderParticipants(data || []);
}

function renderParticipants(list) {
  const attackers = list.filter(p => p.role === 'attacker');
  const defenders = list.filter(p => p.role === 'defender');
  document.getElementById('participants').innerHTML = `
    <div class="participant-list"><h4>Attackers</h4>${attackers.map(p => `<div>${p.kingdom_id}</div>`).join('')}</div>
    <div class="participant-list"><h4>Defenders</h4>${defenders.map(p => `<div>${p.kingdom_id}</div>`).join('')}</div>`;
}

// ✅ Live Polling
function startCombatPolling() {
  stopCombatPolling();
  combatInterval = setInterval(() => {
    if (document.getElementById('tab-live')?.classList.contains('active')) {
      loadCombatLogs();
      loadScoreboard();
    }
  }, 5000);
}
function stopCombatPolling() {
  if (combatInterval) clearInterval(combatInterval);
}

// ✅ Tab Switching

// ✅ Declare War
async function submitDeclareWar() {
  const id = parseInt(document.getElementById('target-alliance-id').value.trim(), 10);
  if (!id) return;
  await fetch('/api/alliance-wars/declare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ defender_alliance_id: id })
  });
  await loadAllianceWars();
  await loadPendingWars();
}

// ✅ Accept Pending
async function loadPendingWars() {
  const container = document.getElementById('pending-wars-list');
  container.innerHTML = 'Loading...';
  const res = await fetch('/api/alliance-wars/list');
  const data = await res.json();
  const pending = (data.upcoming_wars || []).filter(w => w.war_status === 'pending');
  container.innerHTML = pending.length === 0
    ? 'No pending wars.'
    : pending.map(w =>
      `<div>War ${w.alliance_war_id} vs ${w.attacker_alliance_id}
        <button class="accept-war-btn" data-id="${w.alliance_war_id}">Accept</button></div>`
    ).join('');
  document.querySelectorAll('.accept-war-btn').forEach(btn =>
    btn.addEventListener('click', async () => {
      await fetch('/api/alliance-wars/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alliance_war_id: parseInt(btn.dataset.id), action: 'accept' })
      });
      await loadAllianceWars();
      await loadPendingWars();
    }));
}

// ✅ Join/Surrender
async function joinWar(side) {
  await fetch('/api/alliance-wars/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alliance_war_id: currentWarId, side })
  });
  await loadParticipants();
  await loadScoreboard();
}
async function surrenderWar() {
  await fetch('/api/alliance-wars/surrender', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alliance_war_id: currentWarId, side: 'attacker' })
  });
  await loadAllianceWars();
  await viewWarDetails({ alliance_war_id: currentWarId });
}

// ✅ Escape
