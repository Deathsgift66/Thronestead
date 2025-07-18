document.getElementById("js-disabled-message")?.remove();
import { supabase } from '/Javascript/supabaseClient.js';
import { showToast } from '/Javascript/utils.js';

let accessToken = null;
let userId = null;
const UNIT_COUNTERS = { infantry: 'archers', cavalry: 'spearmen', archers: 'infantry', mage: 'infantry' };
const UNIT_ICONS = { infantry: '⚔️', archers: '🏹', cavalry: '🐎', mage: '🧙' };
const TERRAIN_EFFECTS = { forest: 'Defense bonus', river: 'Slows movement', hill: 'Ranged bonus' };
const TERRAIN_COLORS = {
  forest: '#228B22',
  river: '#1E90FF',
  hill: '#8B4513',
  default: 'var(--stone-panel)'
};
function playTickSound() {
  try {
const ctx = new (window.AudioContext || window.webkitAudioContext)();
const osc = ctx.createOscillator();
osc.type = 'square';
osc.frequency.value = 880;
osc.connect(ctx.destination);
osc.start();
osc.stop(ctx.currentTime + 0.1);
  } catch (e) {
console.error('audio', e);
  }
}

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
  const valid = await fetch(`/api/battle/validate-access?war_id=${warId}`, {
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'X-User-ID': userId
}
  });
  if (!valid.ok) {
showToast('Access denied to this battle', 'error');
window.location.href = 'wars.html';
return;
  }
  await refreshBattle();
  subscribeScoreboard();
  pollStatus();
  setInterval(pollStatus, 5000);
  setInterval(refreshBattle, 10000);
});

window.addEventListener('beforeunload', () => {
  if (scoreboardChannel?.unsubscribe) scoreboardChannel.unsubscribe();
});

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
showToast('Failed to load battle status', 'error');
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
  const progress = document.getElementById('tick-progress');
  if (progress) progress.value = ((tickInterval - timer) / tickInterval) * 100;
  if (lastTick !== 0 && timer === tickInterval) {
playTickSound();
refreshBattle();
  }
}

export async function triggerNextTick() {
  try {
const response = await fetch(`/api/battle/next_tick?war_id=${warId}`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'X-User-ID': userId
  }
});
await response.json();
refreshBattle();
  } catch (err) {
console.error('Error triggering next tick:', err);
showToast('Failed to trigger next tick', 'error');
  }
}

export async function refreshBattle() {
  try {
const res = await fetch(`/api/battle/live?war_id=${warId}&since=${logsTick}`, {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'X-User-ID': userId
  }
});
const data = await res.json();
if (data.tile_map) {
  mapWidth = data.map_width;
  mapHeight = data.map_height;
  renderBattleMap(data.tile_map);
}
if (data.units) renderUnits(data.units);
if (data.combat_logs) {
  if (data.combat_logs.length) {
    logsTick = data.combat_logs[data.combat_logs.length - 1].tick_number;
  }
  renderCombatLog(data.combat_logs);
}
if (data.weather) {
  document.getElementById('weather').textContent = data.weather;
  document.getElementById('phase').textContent = data.phase;
  document.getElementById('castle-hp').textContent = data.castle_hp;
  document.getElementById('score-a').textContent = data.attacker_score;
  document.getElementById('score-b').textContent = data.defender_score;
  lastTick = data.battle_tick;
  tickInterval = data.tick_interval_seconds;
}
if (data.victor !== undefined) renderScoreboard(data);
  } catch (err) {
console.error('Error refreshing battle', err);
showToast('Failed to refresh battle data', 'error');
  }
}

let mapWidth = 60;
let mapHeight = 20;
let scoreboardChannel = null;
let tileElements = [];

function renderBattleMap(tileMap) {
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
  const desc = `${type.charAt(0).toUpperCase() + type.slice(1)}: ${TERRAIN_EFFECTS[type] || ''}`;
  tile.title = desc;
  tile.setAttribute('aria-label', desc);
  frag.appendChild(tile);
  tileElements.push(tile);
}
  }
  battleMap.appendChild(frag);
}

function renderUnits(units) {
  if (!tileElements.length) return;
  tileElements.forEach(t => (t.innerHTML = ''));
  units.forEach(unit => {
const index = unit.position_y * mapWidth + unit.position_x;
const tile = tileElements[index];
if (!tile) return;
const unitDiv = document.createElement('div');
unitDiv.className = 'unit-icon';
unitDiv.textContent = UNIT_ICONS[unit.unit_type] || unit.unit_type.charAt(0).toUpperCase();
const counter = UNIT_COUNTERS[unit.unit_type] || 'none';
unitDiv.title = `HP: ${unit.hp ?? '?' }  Morale: ${unit.morale ?? '?' }%  Counters: ${counter}`;
unitDiv.addEventListener('click', () => showOrderPanel(unit));
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
  const auto = document.getElementById('autoscroll');
  if (auto?.checked) logDiv.scrollTop = logDiv.scrollHeight;
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

let activeUnit = null;

export function showOrderPanel(unit) {
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
  const btn = document.getElementById('submit-order-btn');
  if (btn) btn.disabled = true;
  try {
await fetch('/api/battle/orders', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
    'X-User-ID': userId
  },
  body: JSON.stringify({ war_id: warId, unit_id: activeUnit.movement_id, x, y, nonce: Date.now() })
});
closeOrderPanel();
refreshBattle();
  } catch (e) {
console.error('Failed to submit orders', e);
showToast('Failed to submit orders', 'error');
  } finally {
if (btn) btn.disabled = false;
  }
}

window.triggerNextTick = triggerNextTick;
window.refreshBattle = refreshBattle;
window.closeOrderPanel = closeOrderPanel;
window.submitOrders = submitOrders;
