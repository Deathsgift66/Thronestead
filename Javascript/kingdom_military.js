// Project Name: Thronestead©
// File Name: kingdom_military.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';

let currentUserId = null;
let realtimeChannel = null;
let availableUnits = [];

// Initialize logic
document.addEventListener("DOMContentLoaded", async () => {


  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return (window.location.href = "login.html");

  currentUserId = session.user.id;

  subscribeRealtime();
  startAutoRefresh();

  await loadMilitarySummary();
  await loadRecruitableUnits();
  document.getElementById('unit-type-filter')?.addEventListener('change', renderUnits);
  await loadTrainingQueue();
  await loadTrainingHistory();
  updateLastUpdated();
});

// 🔍 Load current troop stats
async function loadMilitarySummary() {
  const container = document.getElementById("military-summary");
  container.innerHTML = "<p>Loading military summary...</p>";

  try {
    const res = await fetch("https://thronestead.onrender.com/api/kingdom_military/summary", { headers: { 'X-User-ID': currentUserId } });
    const data = await res.json();
    container.innerHTML = `
      <p><strong>Total Troops:</strong> ${data.total_troops}</p>
      <p><strong>Base Slots:</strong> ${data.base_slots}</p>
      <p><strong>Used Slots:</strong> ${data.used_slots}</p>
      <p><strong>Morale:</strong> ${data.morale}%</p>
      <p><strong>Usable Slots:</strong> ${data.usable_slots}</p>
    `;
    const bar = document.getElementById('capacity-bar');
    if (bar) {
      bar.querySelector('.progress-bar-fill').style.width = Math.min(100, (data.used_slots * 100) / data.base_slots) + '%';
    }
  } catch (err) {
    console.error("❌ Military summary error:", err);
    container.innerHTML = "<p>Failed to load military summary.</p>";
  }

  updateLastUpdated();
}

// 🧱 Load all eligible units for recruitment
async function loadRecruitableUnits() {
  const container = document.getElementById("unit-list");
  container.innerHTML = "<p>Loading recruitable units...</p>";

  try {
    const res = await fetch("https://thronestead.onrender.com/api/kingdom_military/recruitable", { headers: { 'X-User-ID': currentUserId } });
    const data = await res.json();

    availableUnits = data.units || [];
    populateFilterOptions(availableUnits);
    renderUnits();

  } catch (err) {
    console.error("❌ Recruitable units error:", err);
    container.innerHTML = "<p>Failed to load recruitable units.</p>";
  }
}

// 🧪 Load current training queue
async function loadTrainingQueue() {
  const container = document.getElementById("training-queue");
  container.innerHTML = "<p>Loading training queue...</p>";

  try {
    const res = await fetch("https://thronestead.onrender.com/api/kingdom_military/queue", { headers: { 'X-User-ID': currentUserId } });
    const data = await res.json();

    container.innerHTML = "";

    renderTrainingQueue(data.queue);
  } catch (err) {
    console.error("❌ Training queue error:", err);
    container.innerHTML = "<p>Failed to load training queue.</p>";
  }

  updateLastUpdated();
}

// 🕰️ Load completed training history
async function loadTrainingHistory() {
  const container = document.getElementById("training-history");
  container.innerHTML = "<p>Loading training history...</p>";

  try {
    const res = await fetch("https://thronestead.onrender.com/api/training-history?kingdom_id=1&limit=50", { headers: { 'X-User-ID': currentUserId } });
    const data = await res.json();

    container.innerHTML = renderTrainingHistory(data.history || []);
  } catch (err) {
    console.error("❌ Training history error:", err);
    container.innerHTML = "<p>Failed to load training history.</p>";
  }

  updateLastUpdated();
}

// 📦 Format cost object to string
function formatCost(costObj) {
  if (!costObj || typeof costObj !== "object") return "Unknown";
  return Object.entries(costObj).map(([k, v]) => `${v} ${k}`).join(", ");
}

// 🧼 Sanitize display text

// ⏱ Format timestamps to readable string
function formatTimestamp(ts) {
  if (!ts) return "Unknown";
  const date = new Date(ts);
  return date.toLocaleString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });
}

// 🕓 Update timestamp label
function updateLastUpdated() {
  const el = document.getElementById("last-updated");
  if (el) el.textContent = "Last updated: " + new Date().toLocaleTimeString();
}

// ♻️ Auto-refresh training state
function startAutoRefresh() {
  setInterval(async () => {
    await loadMilitarySummary();
    await loadTrainingQueue();
    updateLastUpdated();
  }, 30000);
}

// 📡 Live Supabase sync for training queue
function subscribeRealtime() {
  realtimeChannel = supabase
    .channel("public:training_queue")
    .on("postgres_changes", { event: "*", schema: "public", table: "training_queue" }, async () => {
      await loadTrainingQueue();
      await loadMilitarySummary();
    })
    .subscribe(status => {
      const indicator = document.getElementById("realtime-indicator");
      if (indicator) {
        indicator.textContent = status === "SUBSCRIBED" ? "Live" : "Offline";
        indicator.className = status === "SUBSCRIBED" ? "connected" : "disconnected";
      }
    });

  window.addEventListener("beforeunload", () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}

// ---------------------------
// 🖼️ Unit Card Renderer and Helpers
// ---------------------------
function renderUnitCard(unit) {
  const gold = unit.cost?.gold || 0;
  const imgName = escapeHTML(unit.unit_name || unit.name);
  return `
    <div class="unit-card border rounded-lg p-4 shadow hover:shadow-lg transition">
      <h3 class="text-xl font-bold">${escapeHTML(unit.name)}</h3>
      <img src="Assets/troops/${imgName}.png" alt="${escapeHTML(unit.name)}" class="w-16 h-16 mx-auto my-2" onerror="this.src='/Assets/icon-sword.svg'; this.onerror=null;" />
      <p><strong>Type:</strong> ${escapeHTML(unit.type)}</p>
      <p><strong>Training:</strong> ${unit.training_time}s</p>
      <p><strong>Cost:</strong> ${gold} gold</p>
      <button class="btn mt-2 recruit-btn" data-unit-id="${unit.id}">Train</button>
    </div>
  `;
}

function populateFilterOptions(units) {
  const select = document.getElementById('unit-type-filter');
  if (!select) return;
  const types = [...new Set(units.map(u => u.type))].sort();
  select.innerHTML = '<option value="">All</option>' +
    types.map(t => `<option value="${escapeHTML(t)}">${escapeHTML(t)}</option>`).join('');
}

function renderUnits() {
  const container = document.getElementById('unit-list');
  if (!container) return;
  const filter = document.getElementById('unit-type-filter')?.value || '';
  let units = availableUnits;
  if (filter) units = units.filter(u => u.type === filter);
  if (!units.length) {
    container.innerHTML = '<p>No recruitable units available.</p>';
    return;
  }
  container.innerHTML = units.map(renderUnitCard).join('');
  container.querySelectorAll('.recruit-btn').forEach(btn => {
    btn.addEventListener('click', () => handleRecruit(btn.dataset.unitId));
  });
}

async function handleRecruit(unitId) {
  const qty = prompt('How many units do you want to recruit?');
  const qtyInt = parseInt(qty);
  if (!qtyInt || qtyInt <= 0) return alert('Invalid quantity.');
  try {
    const res = await fetch('https://thronestead.onrender.com/api/kingdom_military/recruit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': currentUserId },
      body: JSON.stringify({ unit_id: unitId, quantity: qtyInt })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || 'Recruitment failed.');
    alert(result.message || 'Units queued for training.');
    await loadMilitarySummary();
    await loadTrainingQueue();
  } catch (err) {
    console.error('❌ Recruitment error:', err);
    alert(err.message || 'Recruitment failed.');
  }
}

function renderTrainingItem(entry) {
  const unit = availableUnits.find(u => u.name === entry.unit_name) || {};
  const secs = (unit.training_time || 0) * (entry.quantity || 1);
  const endAttr = entry.training_ends_at ? `data-end="${entry.training_ends_at}"` : '';
  return `
    <div class="training-item border p-3 rounded mb-2 shadow-sm" data-seconds="${secs}" ${endAttr}>
      <strong>${escapeHTML(entry.unit_name)} x${entry.quantity}</strong> — ETA: <span class="eta-countdown">${formatTime(secs)}</span>
      <div class="progress-bar-bg mt-1">
        <div class="progress-bar-fill"></div>
      </div>
    </div>
  `;
}

function renderTrainingQueue(queue) {
  const container = document.getElementById('training-queue');
  if (!container) return;
  if (!queue?.length) {
    container.innerHTML = '<p>No active training queue.</p>';
    return;
  }
  container.innerHTML = queue.map(renderTrainingItem).join('');
  updateTrainingCountdowns();
}

function updateTrainingCountdowns() {
  document.querySelectorAll('.training-item').forEach(item => {
    const span = item.querySelector('.eta-countdown');
    const bar = item.querySelector('.progress-bar-fill');
    const end = item.dataset.end ? new Date(item.dataset.end).getTime() : null;
    const baseSecs = parseInt(item.dataset.seconds) || 0;
    item.dataset.start = item.dataset.start || Date.now();
    const start = parseInt(item.dataset.start);
    const total = end ? Math.floor((end - start) / 1000) || baseSecs : baseSecs;
    const remaining = end
      ? Math.max(0, Math.floor((end - Date.now()) / 1000))
      : Math.max(0, Math.floor((start + baseSecs * 1000 - Date.now()) / 1000));
    if (span) span.textContent = formatTime(remaining);
    const pct = total ? Math.max(0, Math.min(100, 100 - (remaining * 100) / total)) : 0;
    if (bar) bar.style.width = pct + '%';
  });
}

setInterval(updateTrainingCountdowns, 1000);

function renderTrainingHistory(logs) {
  const grouped = logs.reduce((acc, entry) => {
    const date = new Date(entry.completed_at).toLocaleDateString();
    acc[date] = acc[date] || [];
    acc[date].push(entry);
    return acc;
  }, {});

  return Object.entries(grouped).map(([date, entries]) => `
    <div class="mb-4">
      <h4 class="font-bold text-lg mb-2">${escapeHTML(date)}</h4>
      <ul class="list-disc ml-5">
        ${entries.map(e => `<li>${e.quantity}x ${escapeHTML(e.unit_name)}</li>`).join('')}
      </ul>
    </div>
  `).join('');
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

setInterval(() => {
  const lastUpdated = new Date().toLocaleTimeString();
  document.getElementById('last-updated').textContent = `Last updated: ${lastUpdated}`;
  const indicator = document.getElementById('realtime-indicator');
  if (indicator) indicator.textContent = '🟢 Live';
}, 30000);
