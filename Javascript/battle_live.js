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

  // Refresh unit positions periodically
  setInterval(loadUnits, 10000);
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
    const response = await fetch(`/api/battle/logs/${warId}`);
    const data = await response.json();
    renderCombatLog(data.combat_logs);
  } catch (err) {
    console.error('Error loading combat logs:', err);
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
