/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_wars.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Modern Card-Based Alliance Wars Board — Matches alliance_wars.html perfectly

import { supabase } from './supabaseClient.js';

let currentWarId = null;
let combatInterval = null;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Initial load
  initTabs();
  await loadCustomBoard();
  await loadAllianceWars();
  await loadPendingWars();
  const declareBtn = document.getElementById('declare-alliance-war-btn');
  if (declareBtn) {
    declareBtn.addEventListener('click', submitDeclareWar);
  }
});

// ✅ Load Alliance Custom Board (image + text)
async function loadCustomBoard() {
  try {
    const res = await fetch("/api/alliance-vault/custom-board");
    const data = await res.json();

    const imgSlot = document.getElementById("custom-image-slot");
    const textSlot = document.getElementById("custom-text-slot");

    imgSlot.innerHTML = data.image_url
      ? `<img src="${data.image_url}" alt="Alliance War Banner" class="war-board-image">`
      : "<p>No custom image set.</p>";

    textSlot.innerHTML = data.custom_text
      ? `<p>${data.custom_text}</p>`
      : "<p>No custom text set.</p>";

  } catch (err) {
    console.error("❌ Error loading custom board:", err);
    document.getElementById("custom-image-slot").innerHTML = "<p>Error loading image.</p>";
    document.getElementById("custom-text-slot").innerHTML = "<p>Error loading text.</p>";
  }
}

// ✅ Load Alliance Wars
async function loadAllianceWars() {
  const container = document.getElementById("wars-container");
  container.innerHTML = "<p>Loading alliance wars...</p>";

  try {
    const res = await fetch("/api/alliance-wars/list");
    const data = await res.json();

    container.innerHTML = "";

    // Render Active Wars
    if (data.active_wars && data.active_wars.length > 0) {
      const activeHeader = document.createElement("h3");
      activeHeader.textContent = "⚔️ Active Wars";
      container.appendChild(activeHeader);

      data.active_wars.forEach(war => {
        const card = document.createElement("div");
        card.classList.add("war-card");

        card.innerHTML = `
          <h4>${war.opponent}</h4>
          <p>Type: <strong>${war.type}</strong></p>
          <p>Status: <strong>${war.status}</strong></p>
          <p>Started: <strong>${war.started}</strong></p>
          <p>Turns Left: <strong>${war.turns_left}</strong></p>
          <div class="war-actions">
            <button class="action-btn view-war-btn" data-war='${JSON.stringify(war)}'>View</button>
          </div>
        `;

        container.appendChild(card);
      });
    } else {
      const noActive = document.createElement("p");
      noActive.textContent = "No active wars.";
      container.appendChild(noActive);
    }

    // Render Past Wars
    if (data.completed_wars && data.completed_wars.length > 0) {
      const pastHeader = document.createElement("h3");
      pastHeader.textContent = "🏅 Past Wars";
      container.appendChild(pastHeader);

      data.completed_wars.forEach(war => {
        const card = document.createElement("div");
        card.classList.add("war-card");

        card.innerHTML = `
          <h4>${war.opponent}</h4>
          <p>Result: <strong>${war.result}</strong></p>
          <p>Ended: <strong>${war.ended}</strong></p>
          <div class="war-actions">
            <button class="action-btn view-war-btn" data-war='${JSON.stringify(war)}'>View</button>
          </div>
        `;

        container.appendChild(card);
      });
    } else {
      const noPast = document.createElement("p");
      noPast.textContent = "No past wars.";
      container.appendChild(noPast);
    }

    // Add View button listeners
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

// ✅ View War Details (Modal or Navigate)
async function viewWarDetails(war) {
  currentWarId = war.alliance_war_id || war.id;
  switchTab('tab-overview');
  try {
    const res = await fetch(`/api/alliance-wars/view?alliance_war_id=${currentWarId}`);
    const data = await res.json();
    renderWarOverview(data.war, data.score);
    renderBattleMap(data.map?.tile_map || []);
    await loadCombatLogs();
    await loadScoreboard();
    await loadParticipants();
    startCombatPolling();
  } catch (err) {
    console.error('Error loading war details:', err);
  }
}

function renderWarOverview(war, score) {
  const container = document.getElementById('war-overview');
  if (!war) {
    container.textContent = 'No data.';
    return;
  }
  container.innerHTML = `
    <p><strong>Attacker:</strong> ${war.attacker_alliance_id}</p>
    <p><strong>Defender:</strong> ${war.defender_alliance_id}</p>
    <p><strong>Status:</strong> ${war.war_status}</p>
    <p><strong>Phase:</strong> ${war.phase}</p>
    <p><strong>Attacker Score:</strong> ${score?.attacker_score ?? 0}</p>
    <p><strong>Defender Score:</strong> ${score?.defender_score ?? 0}</p>
  `;
}

async function loadCombatLogs() {
  if (!currentWarId) return;
  try {
    const res = await fetch(`/api/alliance-wars/combat-log?alliance_war_id=${currentWarId}`);
    const data = await res.json();
    renderCombatLog(data.combat_logs || data.logs || data);
  } catch (err) {
    console.error('Error loading combat logs:', err);
  }
}

function renderBattleMap(tileMap) {
  const battleMap = document.getElementById('battle-map');
  if (!battleMap) return;
  battleMap.innerHTML = '';
  const height = tileMap.length || 20;
  const width = tileMap[0]?.length || 60;
  battleMap.style.gridTemplateColumns = `repeat(${width}, 20px)`;
  for (let r = 0; r < height; r++) {
    for (let c = 0; c < width; c++) {
      const tile = document.createElement('div');
      tile.className = 'tile';
      const type = tileMap[r]?.[c];
      if (type === 'forest') tile.style.backgroundColor = '#228B22';
      else if (type === 'river') tile.style.backgroundColor = '#1E90FF';
      else if (type === 'hill') tile.style.backgroundColor = '#8B4513';
      battleMap.appendChild(tile);
    }
  }
}

function renderCombatLog(logs) {
  const div = document.getElementById('combat-log');
  if (!div) return;
  div.innerHTML = '<strong>Combat Log:</strong><hr>';
  (logs || []).forEach(log => {
    const line = document.createElement('div');
    line.innerText = `[Tick ${log.tick_number}] ${log.event_type} — ${log.notes}`;
    div.appendChild(line);
  });
}

async function loadScoreboard() {
  if (!currentWarId) return;
  try {
    const res = await fetch(`/api/alliance-wars/scoreboard?alliance_war_id=${currentWarId}`);
    const data = await res.json();
    renderScoreboard(data.score || data);
  } catch (err) {
    console.error('Error loading scoreboard:', err);
  }
}

function renderScoreboard(score) {
  const container = document.getElementById('scoreboard');
  if (!container) return;
  if (!score) {
    container.textContent = 'No score data.';
    return;
  }
  container.innerHTML = `
    <table class="score-table">
      <tr><th>Side</th><th>Score</th></tr>
      <tr><td>Attacker</td><td>${score.attacker_score ?? 0}</td></tr>
      <tr><td>Defender</td><td>${score.defender_score ?? 0}</td></tr>
    </table>
  `;
}

async function loadParticipants() {
  if (!currentWarId) return;
  try {
    const { data, error } = await supabase
      .from('alliance_war_participants')
      .select('kingdom_id, role')
      .eq('alliance_war_id', currentWarId);
    if (error) throw error;
    renderParticipants(data);
  } catch (err) {
    console.error('Error loading participants:', err);
  }
}

function renderParticipants(list) {
  const container = document.getElementById('participants');
  if (!container) return;
  if (!list || list.length === 0) {
    container.textContent = 'No participants.';
    return;
  }
  const attackers = list.filter(p => p.role === 'attacker');
  const defenders = list.filter(p => p.role === 'defender');
  container.innerHTML = `
    <div class="participant-list"><h4>Attackers</h4>${attackers.map(p => `<div>${p.kingdom_id}</div>`).join('')}</div>
    <div class="participant-list"><h4>Defenders</h4>${defenders.map(p => `<div>${p.kingdom_id}</div>`).join('')}</div>
  `;
}

function startCombatPolling() {
  stopCombatPolling();
  combatInterval = setInterval(() => {
    if (document.getElementById('tab-live').classList.contains('active')) {
      loadCombatLogs();
      loadScoreboard();
    }
  }, 5000);
}

function stopCombatPolling() {
  if (combatInterval) {
    clearInterval(combatInterval);
    combatInterval = null;
  }
}

function initTabs() {
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });
}

async function submitDeclareWar() {
  const target = document.getElementById('target-alliance-id').value.trim();
  if (!target) return;
  try {
    await fetch('/api/alliance-wars/declare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ defender_alliance_id: parseInt(target) })
    });
    document.getElementById('target-alliance-id').value = '';
    await loadAllianceWars();
    await loadPendingWars();
  } catch (err) {
    console.error('Error declaring alliance war:', err);
  }
}

async function loadPendingWars() {
  const container = document.getElementById('pending-wars-list');
  if (!container) return;
  container.innerHTML = 'Loading...';
  try {
    const res = await fetch('/api/alliance-wars/list');
    const data = await res.json();
    const pending = (data.upcoming_wars || []).filter(w => w.war_status === 'pending');
    container.innerHTML = '';
    if (pending.length === 0) {
      container.textContent = 'No pending wars.';
      return;
    }
    pending.forEach(w => {
      const row = document.createElement('div');
      row.innerHTML = `War ${w.alliance_war_id} vs ${w.attacker_alliance_id === w.defender_alliance_id ? '' : w.attacker_alliance_id} <button class="accept-war-btn" data-id="${w.alliance_war_id}">Accept</button>`;
      container.appendChild(row);
    });
    document.querySelectorAll('.accept-war-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        await fetch('/api/alliance-wars/respond', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ alliance_war_id: parseInt(btn.dataset.id), action: 'accept' })
        });
        await loadAllianceWars();
        await loadPendingWars();
      });
    });
  } catch (err) {
    console.error('Error loading pending wars:', err);
    container.textContent = 'Failed to load.';
  }
}

function switchTab(id) {
  document.querySelectorAll('.tab-button').forEach(b => b.classList.toggle('active', b.dataset.tab === id));
  document.querySelectorAll('.tab-section').forEach(s => s.classList.toggle('active', s.id === id));
  if (id !== 'tab-live') {
    stopCombatPolling();
  }
}
