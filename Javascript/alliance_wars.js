// Project Name: Thronestead©
// File Name: alliance_wars.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { loadCustomBoard } from './customBoard.js';
import { escapeHTML } from './utils.js';
import { setupTabs } from './components/tabControl.js';

let currentWarId = null;
let combatInterval = null;
let lastActivity = 0;
const activityEvents = ['mousemove', 'keydown', 'scroll'];
const activityHandler = () => (lastActivity = Date.now());
let alliances = [];
let switchTab = () => {};
let preplanLoaded = false;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Init
  switchTab = setupTabs({
    onShow: id => {
      if (id !== 'tab-live') stopCombatPolling();
      if (id === 'tab-preplan') loadPreplan();
    }
  });
  await loadCustomBoard({ altText: 'Alliance War Banner' });
  await loadActiveWars();
  await loadWarHistory();
  await loadPendingWars();
  await fetchAlliances();

  const input = document.getElementById('target-alliance-id');
  input.addEventListener('input', e => showAllianceSuggestions(e.target.value));

  document.getElementById('declare-alliance-war-btn')?.addEventListener('click', declareWar);
  document.getElementById('resume-live-btn')?.addEventListener('click', () => {
    document.getElementById('resume-live-btn').hidden = true;
    startCombatPolling();
  });
});




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
  const width = tileMap[0]?.length || 60;
  battleMap.style.gridTemplateColumns = `repeat(${width}, 20px)`;
  tileMap.flat().forEach(type => {
    const tile = document.createElement('div');
    const cls = {
      forest: 'tile-forest',
      river: 'tile-river',
      hill: 'tile-hill'
    }[type];
    tile.className = `tile ${cls || ''}`.trim();
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
  const participants = await Promise.all(
    (data || []).map(async p => {
      try {
        const res = await fetch(`/api/kingdoms/public/${p.kingdom_id}`);
        const info = await res.json();
        return { ...p, name: info.kingdom_name };
      } catch {
        return { ...p, name: `Kingdom ${p.kingdom_id}` };
      }
    })
  );
  renderParticipants(participants);
}

function renderParticipants(list) {
  const attackers = list.filter(p => p.role === 'attacker');
  const defenders = list.filter(p => p.role === 'defender');
  document.getElementById('participants').innerHTML = `
    <div class="participant-list"><h4>Attackers</h4>${attackers
      .map(p => `<div>${escapeHTML(p.name)}</div>`)
      .join('')}</div>
    <div class="participant-list"><h4>Defenders</h4>${defenders
      .map(p => `<div>${escapeHTML(p.name)}</div>`)
      .join('')}</div>`;
}

// ✅ Live Polling
function startCombatPolling() {
  stopCombatPolling();
  lastActivity = Date.now();
  const tab = document.getElementById('tab-live');
  activityEvents.forEach(e => tab?.addEventListener(e, activityHandler));
  combatInterval = setInterval(() => {
    if (!document.getElementById('tab-live')?.classList.contains('active')) return;
    if (Date.now() - lastActivity > 120000) {
      stopCombatPolling();
      const btn = document.getElementById('resume-live-btn');
      if (btn) btn.hidden = false;
      return;
    }
    loadCombatLogs();
    loadScoreboard();
  }, 5000);
}
function stopCombatPolling() {
  if (combatInterval) clearInterval(combatInterval);
  const tab = document.getElementById('tab-live');
  activityEvents.forEach(e => tab?.removeEventListener(e, activityHandler));
}

// ✅ Tab Switching

// ✅ Declare War
async function declareWar() {
  const btn = document.getElementById('declare-alliance-war-btn');
  const name = document.getElementById('target-alliance-id').value.trim();
  const list = document.getElementById('alliance-list');
  const opt = Array.from(list.options).find(o => o.value === name);
  const targetId = opt ? opt.dataset.id : parseInt(name, 10);
  if (!targetId) return;
  btn.disabled = true;
  setTimeout(() => (btn.disabled = false), 3000);
  const res = await fetch('/api/battle/declare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_alliance_id: parseInt(targetId) })
  });
  const data = await res.json();
  if (data.success) loadActiveWars();
}

async function fetchAlliances() {
  try {
    const res = await fetch('/api/diplomacy/alliances');
    const data = await res.json();
    alliances = data.alliances || [];
  } catch (err) {
    console.error('Alliance list error:', err);
  }
}

function showAllianceSuggestions(query) {
  const list = document.getElementById('alliance-list');
  list.innerHTML = '';
  if (!query) return;
  alliances
    .filter(a => a.name.toLowerCase().startsWith(query.toLowerCase()))
    .slice(0, 5)
    .forEach(a => {
      const opt = document.createElement('option');
      opt.value = a.name;
      opt.dataset.id = a.alliance_id;
      list.appendChild(opt);
    });
}

function loadPreplan() {
  if (preplanLoaded) return;
  const container = document.getElementById('preplan-area');
  const frame = document.createElement('iframe');
  frame.src = '/preplan_editor.html';
  frame.loading = 'lazy';
  frame.width = '100%';
  frame.height = '600';
  frame.style.border = 'none';
  container.appendChild(frame);
  preplanLoaded = true;
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
  const container = document.getElementById('wars-container');
  container.innerHTML = wars
    .map(
      w => `
    <div class="war-card" data-id="${w.alliance_war_id}">
      <strong>vs ${escapeHTML(w.enemy_name)}</strong> – Phase: ${escapeHTML(w.phase)}
      <br>Score: ${escapeHTML(String(w.our_score))} vs ${escapeHTML(String(w.their_score))}
      <br><button class="view-war-btn" data-id="${w.alliance_war_id}">Details</button>
    </div>
  `
    )
    .join('');
  container.querySelectorAll('.view-war-btn').forEach(btn =>
    btn.addEventListener('click', () =>
      viewWarDetails({ alliance_war_id: parseInt(btn.dataset.id, 10) })
    )
  );
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

