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
    await loadUnits();
    await loadCombatLogs();
  } catch (err) {
    console.error('Error triggering next tick:', err);
  }
}

// =============================================
// PLACEHOLDER RENDER FUNCTIONS
// =============================================
function renderBattleMap(tileMap) {
  // TODO: Implement your 20x60 grid rendering here
  console.log('Render Battle Map — TODO', tileMap);
}

function renderUnits(units) {
  // TODO: Implement your unit rendering here
  console.log('Render Units — TODO', units);
}

function renderCombatLog(logs) {
  // TODO: Display combat logs in UI
  console.log('Render Combat Log — TODO', logs);
}
