/*
Project Name: Kingmakers Rise Frontend
File Name: battle_live.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Live Battle Viewer — fetches terrain, units and combat logs

import { supabase } from './supabaseClient.js';

// Retrieve war_id from URL (?war_id=123)
const urlParams = new URLSearchParams(window.location.search);
const warId = parseInt(urlParams.get('war_id'), 10) || 0;

document.addEventListener('DOMContentLoaded', async () => {
  await loadTerrain();
  await loadUnits();
  await loadCombatLogs();
  await loadStatus();

  // Refresh unit positions periodically
  setInterval(loadUnits, 10000);
  setInterval(pollStatus, 5000);
});

// =============================================
// LOAD TERRAIN
// =============================================
async function loadTerrain() {
  try {
    const response = await fetch(`/api/battle/terrain/${warId}`);
    const data = await response.json();
    mapWidth = data.map_width;
    mapHeight = data.map_height;
    currentMapColumns = mapWidth;
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
    const response = await fetch(`/api/battle/units/${warId}`);
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
    const response = await fetch(`/api/battle/logs/${warId}?since=${logsTick}`);
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
async function loadStatus() {
  try {
    const res = await fetch(`/api/battle/status/${warId}`);
    const data = await res.json();
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
    loadUnits();
    loadCombatLogs();
  }
}

// =============================================
// OPTIONAL: TRIGGER NEXT TICK (ADMIN TOOL)
// =============================================
export async function triggerNextTick() {
  try {
    const response = await fetch(`/api/battle/next_tick?war_id=${warId}`, {
      method: 'POST'
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
let currentMapColumns = 60;

function renderBattleMap(tileMap) {
  const battleMap = document.getElementById('battle-map');
  battleMap.innerHTML = '';

  battleMap.style.gridTemplateColumns = `repeat(${mapWidth}, 1fr)`;

  for (let row = 0; row < mapHeight; row++) {
    for (let col = 0; col < mapWidth; col++) {
      const tile = document.createElement('div');
      tile.className = 'tile';
      const type = tileMap[row][col];
      if (type === 'forest') tile.style.backgroundColor = '#228B22';
      else if (type === 'river') tile.style.backgroundColor = '#1E90FF';
      else if (type === 'hill') tile.style.backgroundColor = '#8B4513';
      else tile.style.backgroundColor = 'var(--stone-panel)';
      battleMap.appendChild(tile);
    }
  }
}

function renderUnits(units) {
  const battleMap = document.getElementById('battle-map');
  const tiles = battleMap.children;

  for (const tile of tiles) {
    tile.innerHTML = '';
  }

  units.forEach(unit => {
    const index = unit.position_y * mapWidth + unit.position_x;
    if (!tiles[index]) return;
    const unitDiv = document.createElement('div');
    unitDiv.className = 'unit-icon';
    unitDiv.textContent = unit.unit_type.charAt(0).toUpperCase();
    unitDiv.addEventListener('click', () => openOrderPanel(unit));
    tiles[index].appendChild(unitDiv);
  });
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ movement_id: activeUnit.movement_id, position_x: x, position_y: y })
    });
    closeOrderPanel();
    refreshBattle();
  } catch (e) {
    console.error('Failed to submit orders', e);
  }
}
