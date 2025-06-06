/*
Project Name: Kingmakers Rise Frontend
File Name: wars.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Unified War Command Center — Page Controller

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  setupControls();
  await loadWars();
  showToast("Unified War Command Center loaded!");
});

// ✅ Setup Page Controls
function setupControls() {
  // Declare War Button
  document.getElementById('declareWarButton').addEventListener('click', () => {
    openDeclareWarModal();
  });

  // Refresh Wars Button
  document.getElementById('refreshWarsButton').addEventListener('click', async () => {
    showToast("Refreshing active wars...");
    await loadWars();
  });
}

// ✅ Load Active Wars
async function loadWars() {
  const warListEl = document.getElementById('war-list');
  warListEl.innerHTML = "<p>Loading active wars...</p>";

  try {
    const { data: wars, error } = await supabase
      .from('wars')
      .select('*')
      .order('start_date', { descending: true })
      .limit(25);

    if (error) throw error;

    warListEl.innerHTML = "";

    if (wars.length === 0) {
      warListEl.innerHTML = "<p>No active wars at this time.</p>";
      return;
    }

    wars.forEach(war => {
      const card = document.createElement('div');
      card.classList.add('war-card');
      card.innerHTML = `
        <h3>${war.attacker_name} ⚔️ ${war.defender_name}</h3>
        <p>Status: ${war.status}</p>
        <p>Start Date: ${new Date(war.start_date).toLocaleString()}</p>
        <p>Score: ${war.attacker_score} - ${war.defender_score}</p>
        <button class="action-btn" onclick="openWarDetailModal(${war.war_id})">View Details</button>
      `;
      warListEl.appendChild(card);
    });

  } catch (err) {
    console.error("❌ Error loading wars:", err);
    warListEl.innerHTML = "<p>Failed to load active wars.</p>";
    showToast("Failed to load wars.");
  }
}

// ✅ Open Declare War Modal
function openDeclareWarModal() {
  const modal = document.getElementById('declare-war-modal');
  modal.classList.remove('hidden');

  // Inject form if empty
  if (!modal.querySelector('form')) {
    modal.innerHTML = `
      <div class="modal-content">
        <h3>Declare War</h3>
        <form id="declare-war-form">
          <label>Target Kingdom ID:
            <input type="number" id="target-kingdom-id" required />
          </label>
          <label>War Reason:
            <input type="text" id="war-reason" required />
          </label>
          <button type="submit" class="action-btn">Declare</button>
          <button type="button" class="action-btn" onclick="closeDeclareWarModal()">Cancel</button>
        </form>
      </div>
    `;

    // Bind form submit
    document.getElementById('declare-war-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      await submitDeclareWar();
    });
  }
}

// ✅ Close Declare War Modal
function closeDeclareWarModal() {
  const modal = document.getElementById('declare-war-modal');
  modal.classList.add('hidden');
}

// ✅ Submit Declare War
async function submitDeclareWar() {
  const targetId = document.getElementById('target-kingdom-id').value.trim();
  const reason = document.getElementById('war-reason').value.trim();

  if (!targetId || !reason) {
    showToast("Please fill in all fields.");
    return;
  }

  try {
    const res = await fetch("/api/wars/declare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_kingdom_id: parseInt(targetId),
        war_reason: reason
      })
    });

    const result = await res.json();

    if (!res.ok) throw new Error(result.error || "Failed to declare war.");

    showToast("War declared successfully!");
    closeDeclareWarModal();
    await loadWars();

  } catch (err) {
    console.error("❌ Error declaring war:", err);
    showToast("Failed to declare war.");
  }
}

// ✅ Open War Detail Modal
async function openWarDetailModal(warId) {
  const modal = document.getElementById('war-detail-modal');
  modal.classList.remove('hidden');

  modal.innerHTML = `
    <div class="modal-content">
      <h3>War Details</h3>
      <p>Loading war details...</p>
      <button type="button" class="action-btn" onclick="closeWarDetailModal()">Close</button>
    </div>
  `;

  try {
    const { data: war, error } = await supabase
      .from('wars')
      .select('*')
      .eq('war_id', warId)
      .single();

    if (error) throw error;

    const content = modal.querySelector('.modal-content');
    content.innerHTML = `
      <h3>${war.attacker_name} ⚔️ ${war.defender_name}</h3>
      <p>Status: ${war.status}</p>
      <p>Start Date: ${new Date(war.start_date).toLocaleString()}</p>
      <p>Score: ${war.attacker_score} - ${war.defender_score}</p>
      <p>Reason: ${war.war_reason || "Unknown"}</p>
      <button type="button" class="action-btn" onclick="closeWarDetailModal()">Close</button>
    `;

  } catch (err) {
    console.error("❌ Error loading war details:", err);
    showToast("Failed to load war details.");
  }
}

// ✅ Close War Detail Modal
function closeWarDetailModal() {
  const modal = document.getElementById('war-detail-modal');
  modal.classList.add('hidden');
}

// ✅ Toast Helper
function showToast(msg) {
  let toastEl = document.getElementById('toast');
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
