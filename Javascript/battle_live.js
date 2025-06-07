/*
Project Name: Kingmakers Rise Frontend
File Name: battle_live.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Live Battle Viewer — fetches terrain, units and combat logs

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Retrieve war_id from URL (?war_id=123)
const urlParams = new URLSearchParams(window.location.search);
const warId = parseInt(urlParams.get('war_id'), 10) || 0;

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Battle Live Page Loaded');

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
    console.log('Terrain:', data.tile_map);
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
    console.log('Units:', data.units);
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
    console.log('Combat Logs:', data.combat_logs);
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
    const response = await fetch(`/api/battle/next_tick`, {
      method: 'POST'
    });
    const data = await response.json();
    console.log('Next Tick Triggered:', data.message);
    refreshBattle();
  } catch (err) {
    console.error('Error triggering next tick:', err);
  }
}

// =============================================
// PLACEHOLDER RENDER FUNCTIONS
// =============================================
function refreshBattle() {
  loadUnits();
  loadCombatLogs();
}

function renderBattleMap(tileMap) {
  const battleMap = document.getElementById('battle-map');
  battleMap.innerHTML = '';

  for (let row = 0; row < 20; row++) {
    for (let col = 0; col < 60; col++) {
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
    const index = unit.position_y * 60 + unit.position_x;
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
