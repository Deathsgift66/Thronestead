// Project Name: Thronestead©
// File Name: battle_live.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// Live Battle Viewer — fetches terrain, units and combat logs

import { supabase } from './supabaseClient.js';

let accessToken = null;
let userId = null;
const UNIT_COUNTERS = { infantry: "archers", cavalry: "spearmen", archers: "infantry", mage: "infantry" };
const TERRAIN_EFFECTS = { forest: "Defense bonus", river: "Slows movement", hill: "Ranged bonus" };
// Map terrain types to their display colors for quick lookup
const TERRAIN_COLORS = {
  forest: "#228B22",
  river: "#1E90FF",
  hill: "#8B4513",
  default: "var(--stone-panel)"
};
function playTickSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    osc.type = "square";
    osc.frequency.value = 880;
    osc.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.1);
  } catch (e) {
    console.error("audio", e);
  }
}



// Retrieve war_id from URL (?war_id=123)
const urlParams = new URLSearchParams(window.location.search);
const warId = parseInt(urlParams.get('war_id'), 10) || 0;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  accessToken = session.access_token;
  userId = session.user.id;
  await loadTerrain();
  await loadUnits();
  await loadCombatLogs();
  await loadStatus();
  await loadScoreboard();
  subscribeScoreboard();

  // Refresh unit positions periodically
  setInterval(loadUnits, 10000);
  setInterval(pollStatus, 5000);
});

window.addEventListener('beforeunload', () => {
  if (scoreboardChannel) supabase.removeChannel(scoreboardChannel);
});

// =============================================
// LOAD TERRAIN
// =============================================
async function loadTerrain() {
  try {
    const response = await fetch(`/api/battle/terrain/${warId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-User-ID': userId
      }
    });
    const data = await response.json();
    mapWidth = data.map_width;
    mapHeight = data.map_height;
    renderBattleMap(data.tile_map);
  } catch (err) {
    console.error('Error loading terrain:', err);
  }
}

// =============================================
// LOAD UNITS
// =============================================
async function loadUnits() {
  try {
    const response = await fetch(`/api/battle/units/${warId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-User-ID': userId
      }
    });
    const data = await response.json();
    renderUnits(data.units);
  } catch (err) {
    console.error('Error loading units:', err);
  }
}

// =============================================
// LOAD COMBAT LOGS
// =============================================
async function loadCombatLogs() {
  try {
    const response = await fetch(`/api/battle/logs/${warId}?since=${logsTick}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-User-ID': userId
      }
    });
    const data = await response.json();
    if (data.combat_logs.length) {
      logsTick = data.combat_logs[data.combat_logs.length - 1].tick_number;
    }
    renderCombatLog(data.combat_logs);
  } catch (err) {
    console.error('Error loading combat logs:', err);
  }
}

// =============================================
// LOAD STATUS
// =============================================
let lastTick = 0;
let tickInterval = 300;
let logsTick = 0;
let statusData = null;
async function loadStatus() {
  try {
    const res = await fetch(`/api/battle/status/${warId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-User-ID': userId
      }
    });
    const data = await res.json();
    statusData = data;
    lastTick = data.battle_tick;
    tickInterval = data.tick_interval_seconds;
    document.getElementById('weather').textContent = data.weather;
    document.getElementById('phase').textContent = data.phase;
    document.getElementById('castle-hp').textContent = data.castle_hp;
    document.getElementById('score-a').textContent = data.attacker_score;
    document.getElementById('score-b').textContent = data.defender_score;
  } catch (e) {
    console.error('Error loading status', e);
  }
}

function pollStatus() {
  loadStatus().then(() => {
    countdownTick();
  });
}

let timer = tickInterval;
function countdownTick() {
  timer -= 5;
  if (timer <= 0) timer = tickInterval;
  document.getElementById('tick-timer').textContent = `${timer}s`;
  if (lastTick !== 0 && timer === tickInterval) {
    playTickSound();
    loadUnits();
    loadCombatLogs();
    loadScoreboard();
  }
}

// =============================================
// OPTIONAL: TRIGGER NEXT TICK (ADMIN TOOL)
// =============================================
export async function triggerNextTick() {
  try {
    const response = await fetch(`/api/battle/next_tick?war_id=${warId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-User-ID': userId
      }
    });
    const data = await response.json();
    refreshBattle();
  } catch (err) {
    console.error('Error triggering next tick:', err);
  }
}

// =============================================
// RENDER FUNCTIONS
// =============================================
function refreshBattle() {
  loadUnits();
  loadCombatLogs();
}
let mapWidth = 60;
let mapHeight = 20;
let scoreboardChannel = null;
// Cache tile DOM nodes for efficient updates
let tileElements = [];

/**
 * Render the terrain grid using a two-dimensional array of types.
 * Cached tile nodes allow fast unit updates each tick.
 * @param {string[][]} tileMap
 */
function renderBattleMap(tileMap) {
  // Build the battle grid using cached DOM nodes for performance
  const battleMap = document.getElementById('battle-map');
  battleMap.innerHTML = '';
  battleMap.style.gridTemplateColumns = `repeat(${mapWidth}, 1fr)`;
  const frag = document.createDocumentFragment();
  tileElements = [];
  for (let row = 0; row < mapHeight; row++) {
    const rowData = tileMap[row];
    for (let col = 0; col < mapWidth; col++) {
      const tile = document.createElement('div');
      tile.className = 'tile';
      const type = rowData[col];
      const color = TERRAIN_COLORS[type] || TERRAIN_COLORS.default;
      tile.style.backgroundColor = color;
      tile.title = `${type.charAt(0).toUpperCase() + type.slice(1)}: ${TERRAIN_EFFECTS[type] || ''}`;
      frag.appendChild(tile);
      tileElements.push(tile);
    }
  }
  battleMap.appendChild(frag);
}

/**
 * Render all unit icons on the pre-generated grid.
 * @param {Object[]} units
 */
function renderUnits(units) {
  if (!tileElements.length) return;
  tileElements.forEach(t => (t.innerHTML = ''));
  units.forEach(unit => {
    const index = unit.position_y * mapWidth + unit.position_x;
    const tile = tileElements[index];
    if (!tile) return;
    const unitDiv = document.createElement('div');
    unitDiv.className = 'unit-icon';
    unitDiv.textContent = unit.unit_type.charAt(0).toUpperCase();
    const counter = UNIT_COUNTERS[unit.unit_type] || 'none';
    unitDiv.title = `HP: ${unit.hp ?? '?'}  Morale: ${unit.morale ?? '?'}%  Counters: ${counter}`;
    unitDiv.addEventListener('click', () => openOrderPanel(unit));
    tile.appendChild(unitDiv);
    if (unit.morale !== undefined) {
      const morale = document.createElement('div');
      morale.className = 'morale-bar';
      morale.style.width = unit.morale + '%';
      tile.appendChild(morale);
    }
  });

  const fog = document.getElementById('fog-overlay');
  if (statusData?.fog_of_war) {
    fog.style.display = 'block';
  } else {
    fog.style.display = 'none';
  }
}

function renderCombatLog(logs) {
  const logDiv = document.getElementById('combat-log');
  logDiv.innerHTML = '<strong>Combat Log:</strong><hr>';

  logs.slice(-50).forEach(log => {
    const line = document.createElement('div');
    line.innerText = `[Tick ${log.tick_number}] ${log.event_type.toUpperCase()} — ${log.notes} (Damage: ${log.damage_dealt})`;
    logDiv.appendChild(line);
  });
}

// =============================================
// SCOREBOARD (Supabase)
// =============================================
async function loadScoreboard() {
  try {
    const { data, error } = await supabase
      .from('war_scores')
      .select('attacker_score, defender_score, victor')
      .eq('war_id', warId)
      .single();
    if (error) throw error;
    if (data) renderScoreboard(data);
  } catch (err) {
    console.error('Error loading scoreboard:', err);
  }
}

function renderScoreboard(score) {
  if (!score) return;
  document.getElementById('score-attacker').textContent = score.attacker_score;
  document.getElementById('score-defender').textContent = score.defender_score;
  document.getElementById('score-victor').textContent = score.victor || 'TBD';
}

function subscribeScoreboard() {
  scoreboardChannel = supabase
    .channel('public:war_scores')
    .on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'war_scores',
        filter: `war_id=eq.${warId}`
      },
      payload => {
        renderScoreboard(payload.new);
      }
    )
    .subscribe();
}

// =============================================
// ORDER PANEL
// =============================================
let activeUnit = null;

function openOrderPanel(unit) {
  activeUnit = unit;
  document.getElementById('order-unit').textContent = unit.unit_type + ' #' + unit.movement_id;
  document.getElementById('order-x').value = unit.position_x;
  document.getElementById('order-y').value = unit.position_y;
  document.getElementById('order-panel').classList.remove('hidden');
}

function closeOrderPanel() {
  document.getElementById('order-panel').classList.add('hidden');
  activeUnit = null;
}

async function submitOrders() {
  if (!activeUnit) return;
  const x = parseInt(document.getElementById('order-x').value, 10);
  const y = parseInt(document.getElementById('order-y').value, 10);
  try {
    await fetch('/api/battle/orders', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        'X-User-ID': userId
      },
      body: JSON.stringify({ movement_id: activeUnit.movement_id, position_x: x, position_y: y })
    });
    closeOrderPanel();
    refreshBattle();
  } catch (e) {
    console.error('Failed to submit orders', e);
  }
}
