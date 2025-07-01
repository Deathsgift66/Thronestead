// Project Name: Thronestead©
// File Name: village_master.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Sovereign’s Grand Overseer — Page Controller

import { supabase } from '../supabaseClient.js';
import { SovereignUtils } from './sovereign_utils.js';

let realtimeChannel;
let currentKingdomId;

document.addEventListener("DOMContentLoaded", async () => {
  await validateVIPAccess();
  await loadVillages();
  await loadVillageOverview();
  populateMassActionsPanel();
  populateControlsPanel();
  setupAmbientToggle();
  if (currentKingdomId) subscribeVillageRealtime(currentKingdomId);
  showToast("Sovereign’s Grand Overseer loaded!");
});

// ✅ Validate VIP Access - ensure user is VIP Tier 2+
async function validateVIPAccess() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const { data: profile, error } = await supabase
      .from('users')
      .select('vip_tier')
      .eq('user_id', user.id)
      .single();

    if (error) throw error;

    if (!profile.vip_tier || profile.vip_tier < 2) {
      alert("Access Denied: VIP Tier 2 Required.");
      window.location.href = "play.html";
    }
  } catch (err) {
    console.error("❌ Error validating VIP access:", err);
    showToast("Failed to validate VIP access.");
  }
}

// ✅ Load all villages for current kingdom
async function loadVillages() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const { data: profile, error: profileError } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    if (profileError) throw profileError;

    currentKingdomId = profile.kingdom_id;

    const { data: villages, error: villagesError } = await supabase
      .from('villages')
      .select('*')
      .eq('kingdom_id', currentKingdomId)
      .order('village_name', { ascending: true });

    if (villagesError) throw villagesError;

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

  } catch (err) {
    console.error("❌ Error loading villages:", err);
    showToast("Failed to load villages.");
  }
}

// ✅ Populate Mass Actions Panel with async placeholders
function populateMassActionsPanel() {
  const panelEl = document.querySelector('.mass-actions-panel');
  panelEl.innerHTML = `
    <button class="action-btn" onclick="bulkUpgradeAll()">Bulk Upgrade All</button>
    <button class="action-btn" onclick="bulkQueueTraining()">Queue Troops in All Villages</button>
    <button class="action-btn" onclick="bulkHarvest()">Harvest All Resources</button>
  `;
}

// ✅ Populate Controls Panel with filters and sort options
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

// ✅ Setup ambient audio toggle with state feedback
function setupAmbientToggle() {
  const ambientToggle = document.getElementById('ambient-toggle');
  if (!ambientToggle) return;

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

// ✅ Mass Action: Bulk Upgrade All buildings
async function bulkUpgradeAll() {
  showToast("Initiating bulk upgrade of all buildings...");
  try {
    const res = await fetch('/api/village-master/bulk_upgrade', {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed');
    showToast("Bulk upgrade complete!");
  } catch (err) {
    console.error('❌ Bulk upgrade failed:', err);
    showToast('Bulk upgrade failed');
  }
}

// ✅ Mass Action: Queue Troops in all villages
async function bulkQueueTraining() {
  showToast("Queuing troops in all villages...");
  try {
    const res = await fetch('/api/village-master/bulk_queue_training', {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed');
    showToast("Troop training queues started!");
  } catch (err) {
    console.error('❌ Bulk queue failed:', err);
    showToast('Bulk queue failed');
  }
}

// ✅ Mass Action: Harvest all village resources
async function bulkHarvest() {
  showToast("Harvesting resources from all villages...");
  try {
    const res = await fetch('/api/village-master/bulk_harvest', {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed');
    showToast("Resources harvested!");
  } catch (err) {
    console.error('❌ Bulk harvest failed:', err);
    showToast('Bulk harvest failed');
  }
}

// ✅ Filter villages by empty state toggle
function filterVillages() {
  const hideEmpty = document.getElementById('filter-empty-villages').checked;
  const cards = document.querySelectorAll('.village-card');
  cards.forEach(card => {
    const isEmpty = card.getAttribute('data-empty') === "true";
    card.style.display = (hideEmpty && isEmpty) ? "none" : "block";
  });
}

// ✅ Sort villages using SovereignUtils helper
function sortVillages() {
  const sortBy = document.getElementById('sortVillages').value;
  SovereignUtils.sortVillageGrid(sortBy);
}

// ✅ Load Village Overview Stats from API
async function loadVillageOverview() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/village-master/overview', {
      headers: { 'X-User-ID': user.id }
    });
    if (!res.ok) return;
    const data = await res.json();

    const statsEl = document.getElementById('village-stats');
    statsEl.innerHTML = '';

    data.overview.forEach(v => {
      const div = document.createElement('div');
      div.className = 'village-stat';
      div.textContent = `${v.village_name}: buildings ${v.building_count}, levels ${v.total_level}`;
      statsEl.appendChild(div);
    });
  } catch (err) {
    console.error('❌ Error loading village overview:', err);
  }
}

// ✅ Subscribe to real-time village changes for current kingdom
function subscribeVillageRealtime(kingdomId) {
  realtimeChannel = supabase
    .channel('villages-' + kingdomId)
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'kingdom_villages', filter: `kingdom_id=eq.${kingdomId}` },
      async () => {
        await loadVillages();
        await loadVillageOverview();
      }
    )
    .subscribe(status => {
      const ind = document.getElementById('realtime-indicator');
      if (ind) {
        if (status === 'SUBSCRIBED') {
          ind.textContent = 'Live';
          ind.className = 'connected';
        } else {
          ind.textContent = 'Offline';
          ind.className = 'disconnected';
        }
      }
    });

  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}

// ✅ Toast notification helper — reusable throughout your app
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

// Expose key functions for inline handlers
window.bulkUpgradeAll = bulkUpgradeAll;
window.bulkQueueTraining = bulkQueueTraining;
window.bulkHarvest = bulkHarvest;
window.filterVillages = filterVillages;
window.sortVillages = sortVillages;

