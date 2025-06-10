/*
Project Name: Kingmakers Rise Frontend
File Name: battle_replay.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Battle Replay module with timeline playback

import { supabase } from './supabaseClient.js';

const urlParams = new URLSearchParams(window.location.search);
const warId = parseInt(urlParams.get('war_id'), 10) || 0;

let replayData = null;
let currentTick = 0;
let tickInterval = 1000;
let playTimeline = null;
let playbackSpeed = 1;

// ===============================
// DOM READY
// ===============================
document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  await loadReplayData();
  renderTick(0);
  displayOutcome();

  document.getElementById('play-btn').addEventListener('click', animateTimeline);
  document.getElementById('pause-btn').addEventListener('click', () => {
    if (playTimeline) playTimeline.pause();
  });
  document.getElementById('reset-btn').addEventListener('click', resetReplay);
  document.getElementById('replay-timeline').addEventListener('input', e => {
    currentTick = parseInt(e.target.value, 10);
    renderTick(currentTick);
  });
  document.getElementById('speed-select').addEventListener('change', e => {
    playbackSpeed = parseFloat(e.target.value);
    if (playTimeline) {
      playTimeline.timeScale(playbackSpeed);
    }
  });
});

// ===============================
// LOAD REPLAY DATA
// ===============================
export async function loadReplayData() {
  try {
    const res = await fetch(`/api/battle/replay/${warId}`);
    replayData = await res.json();
    tickInterval = replayData.tick_interval_seconds * 1000;
    document.getElementById('replay-timeline').max = replayData.total_ticks;
  } catch (err) {
    console.error('Failed to load replay data', err);
  }
}

// ===============================
// RENDER A SINGLE TICK
// ===============================
export function renderTick(tick) {
  if (!replayData) return;
  const grid = d3.select('#battlefield-grid');
  const tileCount = 20 * 60;
  const tiles = grid.selectAll('div.tile').data(d3.range(tileCount));
  tiles.enter().append('div').attr('class', 'tile');
  tiles.exit().remove();
  grid.selectAll('div.tile').html('');

  const units = replayData.unit_movements.filter(u => u.tick === tick);
  units.forEach(u => {
    const index = u.position_y * 60 + u.position_x;
    const node = grid.selectAll('div.tile').nodes()[index];
    if (node) {
      d3.select(node).append('div').attr('class', 'unit-icon').text(u.icon);
    }
  });

  const logs = replayData.combat_logs.filter(l => l.tick === tick);
  const feed = d3.select('#combat-log-entries').html('');
  logs.forEach(l => {
    feed.append('div').text(`[Tick ${l.tick}] ${l.message}`);
  });

  document.getElementById('replay-timeline').value = tick;
}

// ===============================
// PLAY THE TIMELINE
// ===============================
export function animateTimeline() {
  if (!replayData) return;
  if (playTimeline) playTimeline.kill();
  playTimeline = gsap.timeline({ onComplete: () => { playTimeline = null; } });
  for (let t = currentTick + 1; t <= replayData.total_ticks; t++) {
    playTimeline.to({}, {
      duration: tickInterval / 1000,
      onComplete: () => {
        currentTick = t;
        renderTick(t);
      }
    });
  }
  playTimeline.timeScale(playbackSpeed);
}

// ===============================
// DISPLAY OUTCOME
// ===============================
export function displayOutcome() {
  if (!replayData) return;
  const outcome = replayData.battle_resolution || {};
  document.getElementById('battle-status').textContent = outcome.status || 'Unknown';
  document.getElementById('winner-name').textContent = outcome.winner || 'Unknown';
  document.getElementById('casualties').textContent = outcome.casualties || '0';
  document.getElementById('castle-damage').textContent = outcome.castle_damage || '0';
  document.getElementById('loot').textContent = outcome.loot || 'None';
}

// ===============================
// RESET REPLAY
// ===============================
export function resetReplay() {
  if (playTimeline) playTimeline.kill();
  playTimeline = null;
  currentTick = 0;
  renderTick(0);
}
