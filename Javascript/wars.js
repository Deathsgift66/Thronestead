// Comment
// Project Name: Thronestead©
// File Name: wars.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
// Unified War Command Center — Page Controller
import { escapeHTML } from './utils.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';

import { supabase } from '../supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  setupControls();
  subscribeToWarUpdates();
  await loadWars();
  showToast("Unified War Command Center loaded!");
  applyKingdomLinks();
});

// ✅ Setup Page Controls
function setupControls() {
  const declareWarBtn = document.getElementById('declareWarButton');
  if (declareWarBtn) {
    declareWarBtn.addEventListener('click', openDeclareWarModal);
  }

  const refreshWarsBtn = document.getElementById('refreshWarsButton');
  if (refreshWarsBtn) {
    refreshWarsBtn.addEventListener('click', async () => {
      showToast("Refreshing active wars...");
      await loadWars();
    });
  }
}

// ✅ Subscribe to Supabase real-time updates
function subscribeToWarUpdates() {
  supabase
    .channel('public:wars')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'wars' }, async payload => {
      if (payload.new) {
        appendWarEvent(`${escapeHTML(payload.new.attacker_name)} vs ${escapeHTML(payload.new.defender_name)} — ${escapeHTML(payload.new.status)}`);
      }
      await loadWars();
    })
    .subscribe();
}

// Append a new event message at the top of war feed
function appendWarEvent(msg) {
  const feed = document.getElementById('war-feed');
  if (!feed) return;
  const el = document.createElement('div');
  el.className = 'war-event';
  el.textContent = msg;
  feed.prepend(el);
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
        <h3>${escapeHTML(war.attacker_name)} ⚔️ ${escapeHTML(war.defender_name)}</h3>
        <p class="war-reason">${escapeHTML(war.war_reason || '')}</p>
        <p>Status: ${escapeHTML(war.status)}</p>
        <p>Start: ${new Date(war.start_date).toLocaleString()}</p>
        <p>Score: ${war.attacker_score} - ${war.defender_score}</p>
      `;

      const btn = document.createElement('button');
      btn.className = 'action-btn';
      btn.textContent = 'View Details';
      btn.addEventListener('click', () => openWarDetailModal(war.war_id));
      card.appendChild(btn);

      warListEl.appendChild(card);
    });

  } catch (err) {
    console.error("❌ Error loading wars:", err);
    warListEl.innerHTML = "<p>Failed to load active wars.</p>";
    showToast("Failed to load wars.");
  }
  applyKingdomLinks();
}

// ✅ Open Declare War Modal
function openDeclareWarModal() {
  const modal = document.getElementById('declare-war-modal');
  if (!modal) return;

  modal.classList.remove('hidden');

  if (!modal.querySelector('form')) {
    modal.innerHTML = `
      <div class="modal-content">
        <h3>Declare War</h3>
        <form id="declare-war-form">
          <label for="target-kingdom-id">Target Kingdom ID:</label>
          <input type="number" id="target-kingdom-id" name="target-kingdom-id" required />
          <label for="war-reason">War Reason:</label>
          <input type="text" id="war-reason" name="war-reason" required />
          <button type="submit" class="action-btn">Declare</button>
          <button type="button" class="action-btn" id="declare-war-cancel">Cancel</button>
        </form>
      </div>
    `;

    const form = modal.querySelector('#declare-war-form');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await submitDeclareWar();
    });

    const cancelBtn = modal.querySelector('#declare-war-cancel');
    cancelBtn.addEventListener('click', closeDeclareWarModal);
  }
}

// ✅ Close Declare War Modal
function closeDeclareWarModal() {
  const modal = document.getElementById('declare-war-modal');
  if (modal) modal.classList.add('hidden');
}

// ✅ Submit Declare War
async function submitDeclareWar() {
  const targetInput = document.getElementById('target-kingdom-id');
  const reasonInput = document.getElementById('war-reason');
  const targetId = targetInput?.value.trim();
  const reason = reasonInput?.value.trim();

  if (!targetId || !reason) {
    showToast("Please fill in all fields.");
    return;
  }

  try {
    const res = await fetch("/api/wars/declare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target: parseInt(targetId, 10),
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
  if (!modal) return;

  modal.classList.remove('hidden');
  modal.innerHTML = `
    <div class="modal-content">
      <h3>War Details</h3>
      <p>Loading war details...</p>
      <button type="button" class="action-btn" id="war-detail-close">Close</button>
    </div>
  `;

  const closeBtn = modal.querySelector('#war-detail-close');
  closeBtn.addEventListener('click', closeWarDetailModal);

  try {
    const res = await fetch(`/api/wars/view?war_id=${warId}`);
    if (!res.ok) throw new Error('Failed to load war details');
    const { war } = await res.json();

    const content = modal.querySelector('.modal-content');
    content.innerHTML = `
      <h3>${escapeHTML(war.attacker_name)} ⚔️ ${escapeHTML(war.defender_name)}</h3>
      <p>Status: ${escapeHTML(war.status)}</p>
      <p>Start Date: ${new Date(war.start_date).toLocaleString()}</p>
      <p>Score: ${war.attacker_score} - ${war.defender_score}</p>
      <p>Reason: ${escapeHTML(war.war_reason || "Unknown")}</p>
      <button type="button" class="action-btn" id="war-detail-close-btn">Close</button>
    `;

    content.querySelector('#war-detail-close-btn').addEventListener('click', closeWarDetailModal);
    applyKingdomLinks();

  } catch (err) {
    console.error("❌ Error loading war details:", err);
    showToast("Failed to load war details.");
  }
}

// ✅ Close War Detail Modal
function closeWarDetailModal() {
  const modal = document.getElementById('war-detail-modal');
  if (modal) modal.classList.add('hidden');
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

// ✅ Basic HTML Escape
