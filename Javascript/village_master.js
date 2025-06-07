/*
Project Name: Kingmakers Rise Frontend
File Name: village_master.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Sovereign’s Grand Overseer — Page Controller

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  await validateVIPAccess();
  await loadVillages();
  populateMassActionsPanel();
  populateControlsPanel();
  setupAmbientToggle();
  showToast("Sovereign’s Grand Overseer loaded!");
});

// ✅ Validate VIP Access
async function validateVIPAccess() {
  const { data: { user } } = await supabase.auth.getUser();

  const { data: profile, error } = await supabase
    .from('users')
    .select('vip_tier')
    .eq('user_id', user.id)
    .single();

  if (error) {
    console.error("❌ Error validating VIP access:", error);
    showToast("Failed to validate VIP access.");
    return;
  }

  if (!profile.vip_tier || profile.vip_tier < 2) {
    alert("Access Denied: VIP Tier 2 Required.");
    window.location.href = "play.html";
  }
}

// ✅ Load All Villages
async function loadVillages() {
  const { data: { user } } = await supabase.auth.getUser();

  const { data: profile, error: profileError } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', user.id)
    .single();

  if (profileError) {
    console.error("❌ Error loading profile:", profileError);
    showToast("Failed to load profile.");
    return;
  }

  const kingdomId = profile.kingdom_id;

  const { data: villages, error: villagesError } = await supabase
    .from('villages')
    .select('*')
    .eq('kingdom_id', kingdomId)
    .order('village_name', { ascending: true });

  if (villagesError) {
    console.error("❌ Error loading villages:", villagesError);
    showToast("Failed to load villages.");
    return;
  }

  const gridEl = document.getElementById('village-grid');
  gridEl.innerHTML = "";

  if (villages.length === 0) {
    gridEl.innerHTML = "<p>You do not have any villages.</p>";
    return;
  }

  villages.forEach(village => {
    const card = SovereignUtils.createVillageCard(village);
    gridEl.appendChild(card);
  });
}

// ✅ Populate Mass Actions Panel
function populateMassActionsPanel() {
  const panelEl = document.querySelector('.mass-actions-panel');
  panelEl.innerHTML = `
    <button class="action-btn" onclick="bulkUpgradeAll()">Bulk Upgrade All</button>
    <button class="action-btn" onclick="bulkQueueTraining()">Queue Troops in All Villages</button>
    <button class="action-btn" onclick="bulkHarvest()">Harvest All Resources</button>
  `;
}

// ✅ Populate Controls Panel
function populateControlsPanel() {
  const panelEl = document.querySelector('.controls-panel');
  panelEl.innerHTML = `
    <label>
      <input type="checkbox" id="filter-empty-villages" onchange="filterVillages()"> Hide Empty Villages
    </label>
    <label>
      Sort By:
      <select id="sortVillages" onchange="sortVillages()">
        <option value="name">Name</option>
        <option value="size">Size</option>
        <option value="resources">Resources</option>
      </select>
    </label>
  `;
}

// ✅ Setup Ambient Toggle
function setupAmbientToggle() {
  const ambientToggle = document.getElementById('ambient-toggle');

  ambientToggle.addEventListener('click', () => {
    const isActive = ambientToggle.classList.toggle('active');
    if (isActive) {
      SovereignUtils.playAmbientAudio();
      showToast("Ambient sounds enabled.");
    } else {
      SovereignUtils.stopAmbientAudio();
      showToast("Ambient sounds disabled.");
    }
  });
}

// ✅ Mass Action: Bulk Upgrade All
async function bulkUpgradeAll() {
  showToast("Initiating bulk upgrade of all buildings...");
  // Simulate action — hook to your API
  await new Promise(resolve => setTimeout(resolve, 1000));
  showToast("Bulk upgrade complete!");
}

// ✅ Mass Action: Queue Troops
async function bulkQueueTraining() {
  showToast("Queuing troops in all villages...");
  // Simulate action — hook to your API
  await new Promise(resolve => setTimeout(resolve, 1000));
  showToast("Troop training queues started!");
}

// ✅ Mass Action: Harvest All
async function bulkHarvest() {
  showToast("Harvesting resources from all villages...");
  // Simulate action — hook to your API
  await new Promise(resolve => setTimeout(resolve, 1000));
  showToast("Resources harvested!");
}

// ✅ Filter Villages
function filterVillages() {
  const hideEmpty = document.getElementById('filter-empty-villages').checked;
  const cards = document.querySelectorAll('.village-card');

  cards.forEach(card => {
    const isEmpty = card.getAttribute('data-empty') === "true";
    card.style.display = (hideEmpty && isEmpty) ? "none" : "block";
  });
}

// ✅ Sort Villages
function sortVillages() {
  const sortBy = document.getElementById('sortVillages').value;
  SovereignUtils.sortVillageGrid(sortBy);
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
