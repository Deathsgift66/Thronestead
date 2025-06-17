// Project Name: Thronestead©
// File Name: battle_resolution.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

const urlParams = new URLSearchParams(window.location.search);
const warId = parseInt(urlParams.get('war_id'), 10);

// ===============================
// DOM READY
// ===============================

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  await loadResolution();
  document.getElementById('refresh-btn').addEventListener('click', () => loadResolution());
  setInterval(() => loadResolution(true), 30000);

  // log to audit_log (best effort)
  try {
    await supabase.from('audit_log').insert({
      user_id: session.user.id,
      action: 'view_battle_resolution',
      details: `War ${warId}`
    });
  } catch (e) {
    console.warn('audit log insert failed');
  }
});

// ===============================
// LOAD RESOLUTION DATA
// ===============================
async function loadResolution(silent = false) {
  const summary = document.getElementById('resolution-summary');
  const scoreBox = document.getElementById('score-breakdown');
  const timeline = document.getElementById('combat-timeline');
  const casualty = document.getElementById('casualty-report');
  const lootBox = document.getElementById('loot-summary');
  const participantsBox = document.getElementById('participant-breakdown');
  const statBox = document.getElementById('stat-changes');
  const replayBtn = document.getElementById('replay-button');
  const lastUpdated = document.getElementById('last-updated');

  if (!silent) summary.innerHTML = 'Loading...';
  scoreBox.innerHTML = '';
  timeline.innerHTML = '';
  casualty.innerHTML = '';
  lootBox.innerHTML = '';
  statBox.innerHTML = '';
  participantsBox.innerHTML = '';
  replayBtn.innerHTML = '';

  try {
    const { data: resolution } = await supabase
      .from('battle_resolution_logs')
      .select('*')
      .eq('war_id', warId)
      .single();

    const { data: combatLogs } = await supabase
      .from('combat_logs')
      .select('*')
      .eq('war_id', warId)
      .order('tick_number', { ascending: true });

    const { data: score } = await supabase
      .from('war_scores')
      .select('*')
      .eq('war_id', warId)
      .single();

    const { data: war } = await supabase
      .from('wars_tactical')
      .select('attacker_kingdom_id, defender_kingdom_id')
      .eq('war_id', warId)
      .single();

    const { data: participants } = await supabase
      .from('kingdoms')
      .select('kingdom_id, kingdom_name, military_score, alliance_id')
      .in('kingdom_id', [war.attacker_kingdom_id, war.defender_kingdom_id]);

    const { data: movements } = await supabase
      .from('unit_movements')
      .select('kingdom_id, unit_type, quantity')
      .eq('war_id', warId);

    // Summary Section
    summary.innerHTML = `
      <div class="victory-banner">${resolution.winner_side ? resolution.winner_side.toUpperCase() + ' VICTORY' : 'DRAW'}</div>
      <p>Total Ticks: ${resolution.total_ticks}</p>
    `;

    // Score breakdown
    if (score) {
      scoreBox.innerHTML = `
        <h3>Score Breakdown</h3>
        <p>Attacker: ${score.attacker_score}</p>
        <p>Defender: ${score.defender_score}</p>
      `;
    }

    // Combat timeline
    const logList = document.createElement('ul');
    combatLogs.forEach(log => {
      const li = document.createElement('li');
      li.className = 'combat-log-entry';
      li.textContent = `[Tick ${log.tick_number}] ${log.event_type} - ${log.notes || ''}`;
      logList.appendChild(li);
    });
    timeline.appendChild(logList);

    // Casualties
    casualty.innerHTML = `
      <h3>Casualties</h3>
      <p>Attacker Losses: ${resolution.attacker_casualties}</p>
      <p>Defender Losses: ${resolution.defender_casualties}</p>
    `;

    // Loot summary
    lootBox.innerHTML = '<h3>Loot</h3>';
    const loot = resolution.loot_summary || {};
    const lootList = document.createElement('ul');
    for (const [res, amount] of Object.entries(loot)) {
      const li = document.createElement('li');
      li.innerHTML = `<img class="resource-icon" src="Assets/icons/${res}.png" alt="${res}"> ${res}: ${amount}`;
      lootList.appendChild(li);
    }
    if (lootList.children.length) {
      lootBox.appendChild(lootList);
    } else {
      lootBox.innerHTML += '<p>No loot.</p>';
    }

    if (resolution.rewards) {
      const rewards = document.createElement('div');
      rewards.innerHTML = '<h4>Rewards</h4>';
      const rList = document.createElement('ul');
      for (const [name, val] of Object.entries(resolution.rewards)) {
        const li = document.createElement('li');
        li.textContent = `${name}: ${val}`;
        rList.appendChild(li);
      }
      rewards.appendChild(rList);
      lootBox.appendChild(rewards);
    }

    // Participant breakdown
    participantsBox.innerHTML = '<h3>Participants</h3>';
    const totalUnitsAll = movements.reduce((s, m) => s + (m.quantity || 0), 0) || 1;
    participants.forEach(k => {
      const box = document.createElement('div');
      box.className = 'participant-box';
      const units = movements.filter(m => m.kingdom_id === k.kingdom_id);
      const total = units.reduce((sum, u) => sum + (u.quantity || 0), 0);
      const contrib = ((total / totalUnitsAll) * 100).toFixed(1);
      box.innerHTML = `<strong>${k.kingdom_name}</strong><br>Units Sent: ${total}<br>Contribution: ${contrib}%`;
      participantsBox.appendChild(box);
    });

    // Stat changes
    if (resolution.stat_changes) {
      statBox.innerHTML = '<h3>Stat Changes</h3>';
      const list = document.createElement('ul');
      for (const [stat, val] of Object.entries(resolution.stat_changes)) {
        const li = document.createElement('li');
        li.textContent = `${stat}: ${val > 0 ? '+' : ''}${val}`;
        list.appendChild(li);
      }
      statBox.appendChild(list);
    }

    // Replay button
    replayBtn.innerHTML = `<a href="battle_replay.html?war_id=${warId}" class="royal-button">Replay Battle</a>`;

    lastUpdated.textContent = new Date().toLocaleTimeString();
  } catch (err) {
    console.error('Failed to load battle resolution', err);
    summary.textContent = 'Failed to load resolution data.';
  }
}

