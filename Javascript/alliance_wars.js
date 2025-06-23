// Project Name: Thronestead©
// File Name: alliance_wars.js
// Version 6.16.2025.00.00
// Developer: Codex
import { supabase } from '../supabaseClient.js';
import { loadCustomBoard } from './customBoard.js';
import { escapeHTML } from './utils.js';
import { setupTabs } from './components/tabControl.js';

let currentWarId = null;
let combatInterval = null;
let switchTab = () => {};

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Init
  switchTab = setupTabs({ onShow: id => id !== 'tab-live' && stopCombatPolling() });
  await loadCustomBoard({ altText: 'Alliance War Banner' });
  await loadActiveWars();
  await loadWarHistory();
  await loadPendingWars();

  document.getElementById('declare-alliance-war-btn')?.addEventListener('click', declareWar);
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
async function declareWar() {
  const targetId = document.getElementById('target-alliance-id').value;
  if (!targetId) return;
  const res = await fetch('/api/battle/declare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_alliance_id: parseInt(targetId) })
  });
  const data = await res.json();
  if (data.success) loadActiveWars();
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
      await loadActiveWars();
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
  await loadActiveWars();
  await viewWarDetails({ alliance_war_id: currentWarId });
}

// ✅ Escape

// ---------------------------------------------------------------------------
// Functional JS Hook Points
// ---------------------------------------------------------------------------

// 2. Load Active Wars
async function loadActiveWars() {
  const res = await fetch('/api/battle/wars');
  const wars = await res.json();
  document.getElementById('wars-container').innerHTML = wars
    .map(w => `
    <div class="war-card">
      <strong>vs ${w.enemy_name}</strong> – Phase: ${w.phase}
      <br>Score: ${w.our_score} vs ${w.their_score}
    </div>
  `)
    .join('');
}

// 3. Load War History
async function loadWarHistory() {
  const res = await fetch('/api/battle/history');
  const history = await res.json();
  document.getElementById('history-container').innerHTML = history
    .map(
      entry => `
    <div class="history-entry">
      <strong>${entry.outcome}</strong> – ${entry.enemy_name} on ${new Date(
        entry.ended_at
      ).toLocaleDateString()}
    </div>
  `
    )
    .join('');
}

// 4. Combat Log (Live Battle)
async function pollCombatLog(warId) {
  const res = await fetch(`/api/battle/combat_log/${warId}`);
  const logs = await res.json();
  document.getElementById('combat-log').innerHTML += logs
    .map(l => `<div>${l.timestamp}: ${l.message}</div>`)
    .join('');
}
