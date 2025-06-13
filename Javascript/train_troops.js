/*
Project Name: Kingmakers Rise Frontend
File Name: train_troops.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let accessToken = null;
let userId = null;
let troopLookup = new Map();
let timerHandles = [];

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return window.location.href = 'login.html';

  accessToken = session.access_token;
  userId = session.user.id;

  initToggleButtons();
  await loadGrandMusterHall();
  setInterval(loadGrandMusterHall, 30000);
});

// ✅ UI Toggles
function initToggleButtons() {
  document.getElementById('toggleFilters')?.addEventListener('click', () =>
    document.getElementById('sidebar-panel').classList.toggle('hidden')
  );
  document.getElementById('toggleQueue')?.addEventListener('click', () => {
    document.getElementById('training-queue').classList.toggle('hidden');
    document.getElementById('training-history').classList.toggle('hidden');
  });
}

// ✅ Load All Troop Systems
async function loadGrandMusterHall() {
  const catalogueEl = document.getElementById('troop-catalogue');
  const queueEl = document.getElementById('training-queue');
  const historyEl = document.getElementById('training-history');

  catalogueEl.innerHTML = "<p>Loading troop catalogue...</p>";
  queueEl.innerHTML = "<p>Loading training queue...</p>";
  historyEl.innerHTML = "<p>Loading training history...</p>";

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const { data: userData } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    const kingdomId = userData.kingdom_id;
    const headers = { Authorization: `Bearer ${accessToken}`, 'X-User-ID': userId };

    const troopsRes = await fetch('/api/training_catalog', { headers });
    if (!troopsRes.ok) throw new Error('Failed to load catalog');
    const { catalog } = await troopsRes.json();

    const { data: queue } = await supabase
      .from('training_queue')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .order('training_ends_at', { ascending: true });

    const { data: history } = await supabase
      .from('training_history')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .order('completed_at', { descending: true })
      .limit(20);

    renderTroopCatalogue(catalog);
    renderTrainingQueue(queue || []);
    renderTrainingHistory(history || []);

  } catch (err) {
    console.error("❌ Grand Muster Hall Error:", err);
    showToast("Failed to load troop systems.");
  }
}

// ✅ Catalogue Renderer
function renderTroopCatalogue(troops) {
  const catalogueEl = document.getElementById('troop-catalogue');
  catalogueEl.innerHTML = "";

  if (!troops?.length) {
    catalogueEl.innerHTML = "<p>No troop types available.</p>";
    return;
  }

  troops.forEach(troop => {
    troopLookup.set(troop.unit_id, troop);
    const card = document.createElement("div");
    card.className = "troop-card";
    card.innerHTML = `
      <h3>${escapeHTML(troop.unit_name)}</h3>
      <p>Tier: ${troop.tier}</p>
      <p>Training Time: ${troop.training_time} seconds</p>
      <p>Cost per Unit: ${formatResourceCosts(troop)}</p>
      <button class="action-btn" onclick="trainTroop(${troop.unit_id})">Train 10 Units</button>
    `;
    catalogueEl.appendChild(card);
  });
}

// ✅ Queue Renderer
function renderTrainingQueue(queue) {
  const queueEl = document.getElementById('training-queue');
  queueEl.innerHTML = "";

  if (!queue.length) {
    queueEl.innerHTML = "<p>No troops currently in training queue.</p>";
    return;
  }

  queue.forEach(entry => {
    const card = document.createElement("div");
    card.className = "queue-card";
    const endMs = new Date(entry.training_ends_at).getTime();
    const endsIn = Math.max(0, Math.floor((endMs - Date.now()) / 1000));

    card.dataset.end = endMs;
    card.innerHTML = `
      <h4>${escapeHTML(entry.unit_name)} x ${entry.quantity}</h4>
      <p>Ends In: <span class="countdown">${formatTime(endsIn)}</span></p>
      <button class="action-btn cancel-btn" data-qid="${entry.queue_id}">Cancel</button>
    `;
    queueEl.appendChild(card);
  });

  queueEl.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', () => cancelTraining(+btn.dataset.qid));
  });

  startQueueTimers();
}

// ✅ History Renderer
function renderTrainingHistory(history) {
  const historyEl = document.getElementById('training-history');
  historyEl.innerHTML = "";

  if (!history.length) {
    historyEl.innerHTML = "<p>No completed training history yet.</p>";
    return;
  }

  history.forEach(entry => {
    const card = document.createElement("div");
    card.className = "history-card";
    card.innerHTML = `
      <h4>${escapeHTML(entry.unit_name)} x ${entry.quantity}</h4>
      <p>[${new Date(entry.completed_at).toLocaleString()}] (source: ${escapeHTML(entry.source)})</p>
      ${entry.xp_awarded ? `<p>XP Awarded: ${entry.xp_awarded}</p>` : ""}
    `;
    historyEl.appendChild(card);
  });
}

// ✅ Live Countdown Updates
function startQueueTimers() {
  timerHandles.forEach(clearInterval);
  timerHandles = [];

  document.querySelectorAll('.queue-card[data-end]').forEach(card => {
    const end = +card.dataset.end;
    const span = card.querySelector('.countdown');
    if (!span) return;

    const update = () => {
      const secs = Math.max(0, Math.floor((end - Date.now()) / 1000));
      span.textContent = formatTime(secs);
    };
    update();
    timerHandles.push(setInterval(update, 1000));
  });
}

// ✅ Train Troop Action
async function trainTroop(unitId) {
  if (!confirm("Train 10 units of this troop?")) return;
  try {
    const troop = troopLookup.get(unitId);
    const res = await fetch('/api/training_queue/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
        'X-User-ID': userId
      },
      body: JSON.stringify({
        unit_id: unitId,
        unit_name: troop.unit_name,
        quantity: 10,
        base_training_seconds: troop.training_time || 60
      })
    });

    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Training failed.");
    showToast("Troop training started!");
    await loadGrandMusterHall();

  } catch (err) {
    console.error("❌ Training Error:", err);
    showToast(err.message || "Failed to train troop.");
  }
}

// ✅ Cancel Training
async function cancelTraining(queueId) {
  if (!confirm("Cancel this training order?")) return;
  try {
    const res = await fetch('/api/training_queue/cancel', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
        'X-User-ID': userId
      },
      body: JSON.stringify({ queue_id: queueId })
    });

    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed");
    showToast(result.message || "Training cancelled.");
    await loadGrandMusterHall();

  } catch (err) {
    console.error("❌ Cancel Error:", err);
    showToast(err.message || "Failed to cancel.");
  }
}

// ✅ Format Cost Summary
function formatResourceCosts(troop) {
  const keys = Object.keys(troop).filter(k => k.startsWith("cost_"));
  const costs = keys.map(k => {
    const label = k.replace("cost_", "").replace(/_/g, " ");
    return `${capitalize(label)}: ${troop[k]}`;
  });
  return costs.join(" | ") || "N/A";
}

// ✅ Utilities
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

function showToast(msg) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast-notification";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

function escapeHTML(str) {
  return str?.replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;") || "";
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
