/*
Project Name: Kingmakers Rise Frontend
File Name: train_troops.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Grand Muster Hall — Train Troops Page Controller

import { supabase } from './supabaseClient.js';

let troopLookup = new Map();
let timerHandles = [];

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  initToggleButtons();
  await loadGrandMusterHall();
  setInterval(loadGrandMusterHall, 30000);
});

// ✅ Initialize Toggle Buttons
function initToggleButtons() {
  document.getElementById('toggleFilters').addEventListener('click', () => {
    document.getElementById('sidebar-panel').classList.toggle('hidden');
  });

  document.getElementById('toggleQueue').addEventListener('click', () => {
    const queueSection = document.getElementById('training-queue');
    const historySection = document.getElementById('training-history');
    queueSection.classList.toggle('hidden');
    historySection.classList.toggle('hidden');
  });
}

// ✅ Load Grand Muster Hall
async function loadGrandMusterHall() {
  const catalogueEl = document.getElementById('troop-catalogue');
  const queueEl = document.getElementById('training-queue');
  const historyEl = document.getElementById('training-history');

  // ✅ Clear sections
  catalogueEl.innerHTML = "<p>Loading troop catalogue...</p>";
  queueEl.innerHTML = "<p>Loading training queue...</p>";
  historyEl.innerHTML = "<p>Loading training history...</p>";

  try {
    // ✅ Load user
    const { data: { user } } = await supabase.auth.getUser();

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const kingdomId = userData.kingdom_id;

    // ✅ Load troops from training_catalog
    const { data: troopsData, error: troopsError } = await supabase
      .from('training_catalog')
      .select('*')
      .order('tier', { ascending: true });

    if (troopsError) throw troopsError;

    // ✅ Load training queue
    const { data: queueData, error: queueError } = await supabase
      .from('training_queue')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .order('training_ends_at', { ascending: true });

    if (queueError) throw queueError;

    // ✅ Load training history (assuming a table `training_history`)
    const { data: historyData, error: historyError } = await supabase
      .from('training_history')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .order('completed_at', { descending: true })
      .limit(20);

    if (historyError) throw historyError;

    // ✅ Render sections
    renderTroopCatalogue(troopsData);
    renderTrainingQueue(queueData);
    renderTrainingHistory(historyData);

  } catch (err) {
    console.error("❌ Error loading Grand Muster Hall:", err);
    showToast("Failed to load Grand Muster Hall.");
  }
}

// ✅ Render Troop Catalogue
function renderTroopCatalogue(troops) {
  const catalogueEl = document.getElementById('troop-catalogue');
  catalogueEl.innerHTML = "";

  if (troops.length === 0) {
    catalogueEl.innerHTML = "<p>No troop types available.</p>";
    return;
  }

  troops.forEach(troop => {
    troopLookup.set(troop.unit_id, troop);
    const card = document.createElement("div");
    card.classList.add("troop-card");

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

// ✅ Render Training Queue
function renderTrainingQueue(queue) {
  const queueEl = document.getElementById('training-queue');
  queueEl.innerHTML = "";

  if (queue.length === 0) {
    queueEl.innerHTML = "<p>No troops currently in training queue.</p>";
    return;
  }

  queue.forEach(entry => {
    const card = document.createElement("div");
    card.classList.add("queue-card");

    const endMs = new Date(entry.training_ends_at).getTime();
    const endsIn = Math.max(0, Math.floor((endMs - Date.now()) / 1000));

    card.dataset.end = endMs;
    card.innerHTML = `
      <h4>${escapeHTML(entry.unit_name)} x ${entry.quantity}</h4>
      <p>Ends In: <span class="countdown">${formatTime(endsIn)}</span></p>
    `;

    queueEl.appendChild(card);
  });
  startQueueTimers();
}

// ✅ Render Training History
function renderTrainingHistory(history) {
  const historyEl = document.getElementById('training-history');
  historyEl.innerHTML = "";

  if (history.length === 0) {
    historyEl.innerHTML = "<p>No completed training history yet.</p>";
    return;
  }

  history.forEach(entry => {
    const card = document.createElement("div");
    card.classList.add("history-card");

    card.innerHTML = `
      <h4>${escapeHTML(entry.unit_name)} x ${entry.quantity}</h4>
      <p>[${new Date(entry.completed_at).toLocaleString()}] (source: ${escapeHTML(entry.source)})</p>
      ${entry.xp_awarded ? `<p>XP Awarded: ${entry.xp_awarded}</p>` : ""}
    `;

    historyEl.appendChild(card);
  });
}

function startQueueTimers() {
  timerHandles.forEach(id => clearInterval(id));
  timerHandles = [];
  document.querySelectorAll('.queue-card[data-end]').forEach(card => {
    const end = parseInt(card.dataset.end, 10);
    const span = card.querySelector('.countdown');
    if (!span) return;
    const update = () => {
      const secs = Math.max(0, Math.floor((end - Date.now()) / 1000));
      span.textContent = formatTime(secs);
    };
    update();
    const id = setInterval(update, 1000);
    timerHandles.push(id);
  });
}

// ✅ Train Troop Action
async function trainTroop(unitId) {
  if (!confirm(`Train 10 units of this troop?`)) return;

  try {
    const troop = troopLookup.get(unitId) || {};
    const res = await fetch("/api/training_queue/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        unit_id: unitId,
        unit_name: troop.unit_name,
        quantity: 10,
        base_training_seconds: troop.training_time || 60,
      });
    });

    const result = await res.json();

    if (!res.ok) throw new Error(result.error || "Failed to train troop.");

    showToast("Troop training started!");
    await loadGrandMusterHall();

  } catch (err) {
    console.error("❌ Error training troop:", err);
    showToast(err.message || "Failed to train troop.");
  }
}

// ✅ Helper: Format Resource Costs
function formatResourceCosts(troop) {
  // Assumes troop has fields: cost_gold, cost_food, cost_iron, etc.
  const costs = [];

  if (troop.cost_gold) costs.push(`Gold: ${troop.cost_gold}`);
  if (troop.cost_food) costs.push(`Food: ${troop.cost_food}`);
  if (troop.cost_iron) costs.push(`Iron: ${troop.cost_iron}`);
  if (troop.cost_wood) costs.push(`Wood: ${troop.cost_wood}`);
  if (troop.cost_horses) costs.push(`Horses: ${troop.cost_horses}`);
  // Add more as needed

  return costs.join(" | ") || "N/A";
}

// ✅ Helper: Format Time (seconds → h m s)
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  return `${h}h ${m}m ${s}s`;
}

// ✅ Helper: Toast
function showToast(msg) {
  let toastEl = document.getElementById('toast');

  // Inject toast if not present
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.id = "toast";
    toastEl.className = "toast-notification";
    document.body.appendChild(toastEl);
  }

  toastEl.textContent = msg;
  toastEl.classList.add("show");

  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
}

// ✅ Helper: Escape HTML
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
