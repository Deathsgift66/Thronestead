// Project Name: Thronestead©
// File Name: battle_core.js
// Consolidated battle modules

import { supabase } from '../supabaseClient.js';
import { showToast } from './core_utils.js';
import { authHeaders } from './auth.js';

// ===============================
// PREPLAN EDITOR
// ===============================
export function initPreplanEditor() {
  // Project Name: Thronestead©
  // File Name: preplan_editor.js
  // Version:  7/1/2025 10:38
  // Developer: Deathsgift66
  
  document.addEventListener('DOMContentLoaded', async () => {
    const saveBtn = document.getElementById('save-plan');
    const warInput = document.getElementById('war-id');
    const planArea = document.getElementById('preplan-json');
    const jsonWarning = document.getElementById('json-warning');
    const grid = document.getElementById('preplan-grid');
    const fallbackBtn = document.getElementById('fallback-mode');
    const pathBtn = document.getElementById('path-mode');
    const clearPathBtn = document.getElementById('clear-path');
    const clearFallbackBtn = document.getElementById('clear-fallback');
    const undoBtn = document.getElementById('undo-plan');
    const scoreDiv = document.getElementById('scoreboard-display');
  
    let editMode = null;
    let channel = null;
    let plan = {};
    let lastSavedPlan = {};
  
    function updateModeButtons() {
      fallbackBtn.classList.toggle('active', editMode === 'fallback');
      pathBtn.classList.toggle('active', editMode === 'path');
    }
  
    // ✅ Render the battlefield grid
    function renderGrid() {
      grid.innerHTML = '';
      for (let y = 0; y < 20; y++) {
        for (let x = 0; x < 60; x++) {
          const tile = document.createElement('div');
          tile.className = 'grid-tile';
          tile.dataset.x = x;
          tile.dataset.y = y;
  
          // Highlight based on current plan
          if (plan.patrol_path?.some(p => p.x === x && p.y === y)) {
            tile.classList.add('path');
          }
          if (plan.fallback_point?.x === x && plan.fallback_point?.y === y) {
            tile.classList.add('fallback');
          }
  
          tile.addEventListener('click', () => handleTileClick(x, y));
          grid.appendChild(tile);
        }
      }
    }
  
    // ✅ Handle tile click based on current mode
    function handleTileClick(x, y) {
      if (editMode === 'fallback') {
        plan.fallback_point = { x, y };
      } else if (editMode === 'path') {
        plan.patrol_path ??= [];
        plan.patrol_path.push({ x, y });
      }
      updatePlanArea();
      renderGrid();
    }
  
    // ✅ Sync JSON view with plan object
    function updatePlanArea() {
      planArea.value = JSON.stringify(plan, null, 2);
    }
  
    function validatePlan(p) {
      if (p.fallback_point) {
        const f = p.fallback_point;
        if (typeof f.x !== 'number' || typeof f.y !== 'number') return false;
      }
      if (p.patrol_path) {
        if (!Array.isArray(p.patrol_path)) return false;
        for (const node of p.patrol_path) {
          if (typeof node.x !== 'number' || typeof node.y !== 'number') return false;
        }
      }
      return true;
    }
  
    // ✅ Load the pre-existing plan for this war
    async function loadPlan() {
      const warId = warInput.value;
      if (!warId) return;
      try {
        const res = await fetch(`/api/alliance-wars/preplan?alliance_war_id=${warId}`);
        const data = await res.json();
        plan = data.plan || {};
        lastSavedPlan = JSON.parse(JSON.stringify(plan));
        updatePlanArea();
        renderGrid();
      } catch (err) {
        console.error('❌ Failed to load preplan:', err);
      }
    }
  
    // ✅ Update scoreboard display
    async function updateScoreDisplay(score) {
      if (score) {
        scoreDiv.textContent = `${score.attacker_score} - ${score.defender_score}`;
      }
    }
  
    // ✅ Subscribe to live score updates via Supabase channel
    async function loadScore() {
      const warId = warInput.value;
      if (!warId) return;
      try {
        const { data, error } = await supabase
          .from('alliance_war_scores')
          .select('attacker_score, defender_score')
          .eq('alliance_war_id', warId)
          .maybeSingle();
        if (!error) updateScoreDisplay(data);
  
        if (channel?.unsubscribe) await channel.unsubscribe();
  
        channel = supabase
          .channel('war_scores_' + warId)
          .on(
            'postgres_changes',
            {
              event: '*',
              schema: 'public',
              table: 'alliance_war_scores',
              filter: `alliance_war_id=eq.${warId}`
            },
            payload => updateScoreDisplay(payload.new)
          )
          .subscribe();
      } catch (err) {
        console.error('❌ Failed to load score:', err);
      }
    }
  
    // ✅ Button bindings
    fallbackBtn.addEventListener('click', () => {
      editMode = 'fallback';
      updateModeButtons();
    });
    pathBtn.addEventListener('click', () => {
      editMode = 'path';
      updateModeButtons();
    });
    clearPathBtn.addEventListener('click', () => {
      plan.patrol_path = [];
      renderGrid();
      updatePlanArea();
    });
    clearFallbackBtn.addEventListener('click', () => {
      delete plan.fallback_point;
      renderGrid();
      updatePlanArea();
    });
    undoBtn.addEventListener('click', () => {
      plan = JSON.parse(JSON.stringify(lastSavedPlan));
      renderGrid();
      updatePlanArea();
    });
  
    // ✅ Listen for manual JSON edits
    planArea.addEventListener('input', () => {
      try {
        const parsed = JSON.parse(planArea.value || '{}');
        if (!validatePlan(parsed)) throw new Error('invalid');
        plan = parsed;
        jsonWarning.style.display = 'none';
        renderGrid();
      } catch {
        jsonWarning.textContent = 'Invalid JSON';
        jsonWarning.style.display = 'block';
      }
    });
  
    // ✅ Save the preplan to backend with simple debounce
    let saveCooldown = false;
    saveBtn.addEventListener('click', async () => {
      if (saveCooldown) return;
      saveCooldown = true;
      saveBtn.disabled = true;
      setTimeout(() => (saveCooldown = false), 1000);
      const warId = parseInt(warInput.value, 10);
      if (!warId) {
        showToast('Enter valid War ID', 'error');
        saveBtn.disabled = false;
        return;
      }
      if (!validatePlan(plan)) {
        showToast('Plan JSON invalid', 'error');
        saveBtn.disabled = false;
        return;
      }
  
      try {
        const res = await fetch('/api/alliance-wars/preplan/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            alliance_war_id: warId,
            preplan_jsonb: plan
          })
        });
  
        if (!res.ok) throw new Error('Save failed');
        lastSavedPlan = JSON.parse(JSON.stringify(plan));
        showToast('Plan saved!', 'success');
      } catch (err) {
        console.error('❌ Error saving plan:', err);
        showToast('Save failed', 'error');
      } finally {
        saveBtn.disabled = false;
      }
    });
  
    // ✅ Reload plan and score when War ID changes
    warInput.addEventListener('change', async () => {
      await loadPlan();
      await loadScore();
    });
  
    // ✅ Initial run
    await loadPlan();
    await loadScore();
    updateModeButtons();
  });
}

// ===============================
// BATTLE LIVE
// ===============================
export function initBattleLive() {
  
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
  async function triggerNextTick() {
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
  async function refreshBattle() {
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
  function showOrderPanel(unit) {
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
}

// ===============================
// BATTLE REPLAY
// ===============================
export function initBattleReplay() {
  // Project Name: Thronestead©
  // File Name: battle_replay.js
  // Version:  7/1/2025 10:38
  // Developer: Deathsgift66
  // Battle Replay module with timeline playback
  
  
  const urlParams = new URLSearchParams(window.location.search);
  const warId = parseInt(urlParams.get('war_id'), 10) || 0;
  
  let replayData = null;
  let currentTick = 0;
  let tickInterval = 1000;
  let playTimeline = null;
  let playbackInterval = null; // legacy interval fallback
  let playbackSpeed = 1;
  
  function togglePlayButtons(isPlaying) {
    document.getElementById('play-btn').disabled = isPlaying;
    document.getElementById('pause-btn').disabled = !isPlaying;
  }
  
  // ===============================
  // DOM READY
  // ===============================
  let realtimeSub;
  document.addEventListener('DOMContentLoaded', async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      window.location.href = 'login.html';
      return;
    }
  
    const timeline = document.getElementById('replay-timeline');
    if (timeline) timeline.disabled = true;
  
    await loadReplay();
    if (timeline) timeline.disabled = false;
  
    renderTick(0);
    displayOutcome();
    togglePlayButtons(false);
  
    realtimeSub = supabase
      .channel(`replay_${warId}`)
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'combat_logs', filter: `war_id=eq.${warId}` }, payload => {
        if (!replayData) return;
        replayData.combat_logs.push({
          tick: payload.new.tick_number,
          message: payload.new.notes || payload.new.event_type,
          attacker_unit_id: payload.new.attacker_unit_id,
          defender_unit_id: payload.new.defender_unit_id,
          position_x: payload.new.position_x,
          position_y: payload.new.position_y,
          damage_dealt: payload.new.damage_dealt
        });
        if (payload.new.tick_number === currentTick) renderTick(currentTick);
      })
      .subscribe();
  
    document.getElementById('play-btn').addEventListener('click', () => play(playbackSpeed));
    document.getElementById('pause-btn').addEventListener('click', pause);
    document.getElementById('reset-btn').addEventListener('click', reset);
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
  
  window.addEventListener('beforeunload', () => {
    realtimeSub?.unsubscribe();
  });
  
  // ===============================
  // LOAD REPLAY DATA
  // ===============================
  export async function loadReplay() {
    try {
      const headers = await authHeaders();
      const res = await fetch(`/api/battle/replay/${warId}`, { headers });
      replayData = await res.json();
      tickInterval = (replayData.tick_interval_seconds ?? 1) * 1000;
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
        d3.select(node)
          .append('div')
          .attr('class', 'unit-icon')
          .text(u.icon)
          .attr('title', `HP: ${u.hp ?? '?'}  Morale: ${u.morale ?? '?'}%`);
        if (u.morale !== undefined) {
          d3.select(node)
            .append('div')
            .attr('class', 'morale-bar')
            .style('width', `${u.morale}%`);
        }
      }
    });
  
    const fog = document.getElementById('fog-overlay');
    if (replayData?.fog_of_war === true) {
      fog.style.display = 'block';
    } else {
      fog.style.display = 'none';
    }
  
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
  export function play(speed = playbackSpeed) {
    if (!replayData) return;
    if (playTimeline) playTimeline.kill();
    playTimeline = gsap.timeline({ onComplete: () => { playTimeline = null; togglePlayButtons(false); } });
    for (let t = currentTick + 1; t <= replayData.total_ticks; t++) {
      playTimeline.to({}, {
        duration: tickInterval / 1000,
        onComplete: () => {
          currentTick = t;
          renderTick(t);
        }
      });
    }
    playTimeline.timeScale(speed);
    togglePlayButtons(true);
  }
  
  export function pause() {
    if (playTimeline) playTimeline.pause();
    clearInterval(playbackInterval);
    togglePlayButtons(false);
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
  export function reset() {
    if (playTimeline) playTimeline.kill();
    playTimeline = null;
    currentTick = 0;
    renderTick(0);
    const fog = document.getElementById('fog-overlay');
    if (fog) fog.style.display = replayData?.fog_of_war === true ? 'block' : 'none';
    togglePlayButtons(false);
  }
}

// ===============================
// BATTLE RESOLUTION
// ===============================
export function initBattleResolution() {
  // Project Name: Thronestead©
  // File Name: battle_resolution.js
  // Version:  7/21/2025 12:30
  // Developer: Deathsgift66
  
  let accessToken = null;
  let userId = null;
  
  // ===============================
  // DOM READY
  // ===============================
  
  document.addEventListener('DOMContentLoaded', async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      window.location.href = 'login.html';
      return;
    }
    accessToken = session.access_token;
    userId = session.user.id;
  
    const warId = getWarIdFromURL();
    if (warId === null) {
      return;
    }
    await fetchBattleResolution(warId);
  
    document.getElementById('refresh-btn').addEventListener('click', () => {
      const id = getWarIdFromURL();
      if (id !== null) {
        fetchBattleResolution(id);
      }
    });
    document.getElementById('view-replay-btn').addEventListener('click', () => {
      const id = getWarIdFromURL();
      if (id !== null) {
        window.location.href = `/battle_replay.html?war_id=${id}`;
      }
    });
    setInterval(() => {
      const id = getWarIdFromURL();
      if (id !== null) {
        fetchBattleResolution(id);
      }
    }, 30000);
  
    // log to audit_log (best effort)
    try {
      await supabase.from('audit_log').insert({
        user_id: session.user.id,
        action: 'view_battle_resolution',
        details: `War ${warId}`
      });
    } catch {
      console.warn('audit log insert failed');
    }
  });
  
  // ===============================
  // LOAD RESOLUTION DATA
  // ===============================
  async function fetchBattleResolution(warId) {
    document.getElementById('resolution-summary').innerHTML = '<p>Loading results...</p>';
    const res = await fetch(`/api/battle/resolution?war_id=${warId}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-User-ID': userId
      }
    });
    if (!res.ok) {
      document.getElementById('resolution-summary').textContent = '❌ Failed to load battle results.';
      return;
    }
    const data = await res.json();
    renderResolutionData(data);
    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
  }
  
  function renderResolutionData(data) {
    const summary = document.getElementById('resolution-summary');
    const scoreBox = document.getElementById('score-breakdown');
    const timeline = document.getElementById('combat-timeline');
    const casualty = document.getElementById('casualty-report');
    const lootBox = document.getElementById('loot-summary');
    const participantsBox = document.getElementById('participant-breakdown');
    const statBox = document.getElementById('stat-changes');
  
    summary.innerHTML = `
      <h3>Victory: ${data.winner}</h3>
      <p>Battle Duration: ${data.duration_ticks} ticks</p>
      <p>Victor Score: ${data.victor_score}</p>
    `;
  
    casualty.innerHTML = renderCasualties(data.casualties);
    lootBox.innerHTML = renderLoot(data.loot);
  
    if (data.score_breakdown) {
      scoreBox.innerHTML = `<pre>${JSON.stringify(data.score_breakdown, null, 2)}</pre>`;
    }
  
    if (Array.isArray(data.timeline)) {
      const list = document.createElement('ul');
      data.timeline.forEach(t => {
        const li = document.createElement('li');
        li.className = 'combat-log-entry';
        li.textContent = t;
        list.appendChild(li);
      });
      timeline.innerHTML = '';
      timeline.appendChild(list);
    }
  
    if (data.stat_changes) {
      const list = document.createElement('ul');
      for (const [k, v] of Object.entries(data.stat_changes)) {
        const li = document.createElement('li');
        li.textContent = `${k}: ${v}`;
        list.appendChild(li);
      }
      statBox.innerHTML = '';
      statBox.appendChild(list);
    }
  
    if (data.participants) {
      participantsBox.innerHTML = '';
      for (const [side, names] of Object.entries(data.participants)) {
        const div = document.createElement('div');
        div.className = 'participant-box';
        div.innerHTML = `<strong>${side}</strong>: ${names.join(', ')}`;
        participantsBox.appendChild(div);
      }
    }
  
    document.getElementById('replay-button').innerHTML =
      `<a href="battle_replay.html?war_id=${getWarIdFromURL()}" class="royal-button">Replay Battle</a>`;
  }
  
  function renderCasualties(c) {
    if (!c) return '';
    const div = document.createElement('div');
    div.innerHTML = '<h3>Casualties</h3>';
    for (const [side, obj] of Object.entries(c)) {
      const p = document.createElement('p');
      const count = Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ');
      p.textContent = `${side}: ${count}`;
      div.appendChild(p);
    }
    return div.innerHTML;
  }
  
  function renderLoot(loot) {
    if (!loot) return '';
    const div = document.createElement('div');
    div.innerHTML = '<h3>Loot</h3>';
    const ul = document.createElement('ul');
    for (const [res, amount] of Object.entries(loot)) {
      const li = document.createElement('li');
      li.textContent = `${res}: ${amount}`;
      ul.appendChild(li);
    }
    div.appendChild(ul);
    return div.innerHTML;
  }
  
  function getWarIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    const warId = parseInt(params.get('war_id'), 10);
    if (isNaN(warId)) {
      alert('⚠ Invalid war ID');
      return null;
    }
    return warId;
  }
  
}

