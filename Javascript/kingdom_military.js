/*
Project Name: Kingmakers Rise Frontend
File Name: kingdom_military.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let currentUserId = null;
let realtimeChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }
  currentUserId = session.user.id;

  subscribeRealtime();
  startAutoRefresh();

  // ✅ Initial load
  await loadMilitarySummary();
  await loadRecruitableUnits();
  await loadTrainingQueue();
  await loadTrainingHistory();
  updateLastUpdated();
});

// ✅ Load Military Summary
async function loadMilitarySummary() {
  const container = document.getElementById("military-summary");
  container.innerHTML = "<p>Loading military summary...</p>";

  try {
    const res = await fetch("/api/kingdom_military/summary", { headers: { 'X-User-ID': currentUserId } });
    const data = await res.json();

    container.innerHTML = `
      <p><strong>Total Troops:</strong> ${data.total_troops}</p>
      <p><strong>Base Slots:</strong> ${data.base_slots}</p>
      <p><strong>Used Slots:</strong> ${data.used_slots}</p>
      <p><strong>Morale:</strong> ${data.morale}%</p>
      <p><strong>Usable Slots:</strong> ${data.usable_slots}</p>
    `;
  } catch (err) {
    console.error("❌ Error loading military summary:", err);
    container.innerHTML = "<p>Failed to load military summary.</p>";
  }
  updateLastUpdated();
}

// ✅ Load Recruitable Units
async function loadRecruitableUnits() {
  const container = document.getElementById("unit-list");
  container.innerHTML = "<p>Loading recruitable units...</p>";

  try {
    const res = await fetch("/api/kingdom_military/recruitable", { headers: { 'X-User-ID': currentUserId } });
    const data = await res.json();

    container.innerHTML = "";

    if (!data.units || data.units.length === 0) {
      container.innerHTML = "<p>No recruitable units available.</p>";
      return;
    }

    data.units.forEach(unit => {
      const card = document.createElement("div");
      card.classList.add("unit-card");

      card.innerHTML = `
        <h4>${escapeHTML(unit.name)}</h4>
        <p>Type: ${escapeHTML(unit.type)}</p>
        <p>Cost: ${formatCost(unit.cost)}</p>
        <p>Training Time: ${unit.training_time} seconds</p>
        <button class="action-btn recruit-btn" data-unit-id="${unit.id}">Recruit</button>
      `;

      container.appendChild(card);
    });

    // ✅ Bind Recruit buttons
    document.querySelectorAll(".recruit-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const unitId = btn.dataset.unitId;
        const qty = prompt("How many units do you want to recruit?");
        const qtyInt = parseInt(qty);

        if (!qtyInt || qtyInt <= 0) {
          alert("Invalid quantity.");
          return;
        }

        try {
          const res = await fetch("/api/kingdom_military/recruit", {
            method: "POST",
            headers: { "Content-Type": "application/json", 'X-User-ID': currentUserId },
            body: JSON.stringify({ unit_id: unitId, quantity: qtyInt })
          });

          const result = await res.json();

          if (!res.ok) {
            throw new Error(result.error || "Recruitment failed.");
          }

          alert(result.message || "Units queued for training.");
          await loadMilitarySummary();
          await loadTrainingQueue();
        } catch (err) {
          console.error("❌ Error recruiting units:", err);
          alert(err.message || "Recruitment failed.");
        }
      });
    });

  } catch (err) {
    console.error("❌ Error loading recruitable units:", err);
    container.innerHTML = "<p>Failed to load recruitable units.</p>";
  }
}

// ✅ Load Training Queue
async function loadTrainingQueue() {
  const container = document.getElementById("training-queue");
  container.innerHTML = "<p>Loading training queue...</p>";

  try {
    const res = await fetch("/api/kingdom_military/queue", { headers: { 'X-User-ID': currentUserId } });
    const data = await res.json();

    container.innerHTML = "";

    if (!data.queue || data.queue.length === 0) {
      container.innerHTML = "<p>No active training queue.</p>";
      return;
    }

    const list = document.createElement("ul");

    data.queue.forEach(entry => {
      const li = document.createElement("li");
      li.textContent = `${escapeHTML(entry.unit_name)} x${entry.quantity} — Ends: ${formatTimestamp(entry.training_ends_at)}`;

      // Optional: add Dismiss button here if desired
      list.appendChild(li);
    });

    container.appendChild(list);
  } catch (err) {
    console.error("❌ Error loading training queue:", err);
    container.innerHTML = "<p>Failed to load training queue.</p>";
  }
  updateLastUpdated();
}

// ✅ Load Training History
async function loadTrainingHistory() {
  const container = document.getElementById("training-history");
  container.innerHTML = "<p>Loading training history...</p>";

  try {
    const res = await fetch("/api/training-history?kingdom_id=1&limit=50", { headers: { 'X-User-ID': currentUserId } });
    const data = await res.json();

    container.innerHTML = "";

    if (!data.history || data.history.length === 0) {
      container.innerHTML = "<p>No training history available.</p>";
      return;
    }

    const list = document.createElement("ul");

    data.history.forEach(entry => {
      const li = document.createElement("li");
      li.textContent = `[${formatTimestamp(entry.completed_at)}] Trained ${entry.quantity} ${escapeHTML(entry.unit_name)} (source: ${entry.source})`;
      list.appendChild(li);
    });

    container.appendChild(list);
  } catch (err) {
    console.error("❌ Error loading training history:", err);
    container.innerHTML = "<p>Failed to load training history.</p>";
  }
  updateLastUpdated();
}

// ✅ Format Cost
function formatCost(costObj) {
  if (!costObj || typeof costObj !== "object") return "Unknown";
  return Object.entries(costObj).map(([resource, amount]) => `${amount} ${resource}`).join(", ");
}

// ✅ Format Timestamp
function formatTimestamp(ts) {
  if (!ts) return "Unknown";
  const date = new Date(ts);
  return date.toLocaleString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });
}

// ✅ Basic HTML escape
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function updateLastUpdated() {
  const el = document.getElementById('last-updated');
  if (el) el.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
}

function startAutoRefresh() {
  setInterval(() => {
    loadMilitarySummary();
    loadTrainingQueue();
    updateLastUpdated();
  }, 30000);
}

function subscribeRealtime() {
  realtimeChannel = supabase
    .channel('public:training_queue')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'training_queue' }, () => {
      loadTrainingQueue();
      loadMilitarySummary();
    })
    .subscribe(status => {
      const indicator = document.getElementById('realtime-indicator');
      if (indicator) {
        if (status === 'SUBSCRIBED') {
          indicator.textContent = 'Live';
          indicator.className = 'connected';
        } else {
          indicator.textContent = 'Offline';
          indicator.className = 'disconnected';
        }
      }
    });

  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}
