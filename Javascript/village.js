/*
Project Name: Kingmakers Rise Frontend
File Name: village.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Royal Hamlet Ledger — Village Page Controller

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  await loadVillagePage();
});

// ✅ Load Full Village Page
async function loadVillagePage() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const villageId = urlParams.get('village_id');

    if (!villageId) {
      showToast("Invalid village ID.");
      return;
    }

    // ✅ Load village data
    const { data: village, error: villageError } = await supabase
      .from('villages')
      .select('*')
      .eq('village_id', villageId)
      .single();

    if (villageError) throw villageError;

    // ✅ Update Village Banner
    document.getElementById('village-name').textContent = village.village_name;

    // ✅ Load resources
    await loadVillageResources(villageId);

    // ✅ Load buildings
    await loadVillageBuildings(villageId);

    // ✅ Load modifiers
    await loadVillageModifiers(villageId);

    // ✅ Load military
    await loadVillageMilitary(villageId);

    // ✅ Load queue
    await loadVillageQueue(villageId);

    // ✅ Load event log
    await loadVillageEvents(villageId);

    showToast("Village loaded!");

  } catch (err) {
    console.error("❌ Error loading village:", err);
    showToast("Failed to load village.");
  }
}

// ✅ Load Resources
async function loadVillageResources(villageId) {
  const gridEl = document.getElementById('resource-grid');
  gridEl.innerHTML = "<p>Loading resources...</p>";

  const { data: resData, error } = await supabase
    .from('village_resources')
    .select('*')
    .eq('village_id', villageId)
    .single();

  if (error) {
    console.error("❌ Error loading resources:", error);
    gridEl.innerHTML = "<p>Failed to load resources.</p>";
    return;
  }

  gridEl.innerHTML = "";

  Object.keys(resData).forEach(key => {
    if (key === 'village_id') return;

    const card = document.createElement('div');
    card.classList.add('resource-card');
    card.innerHTML = `
      <h4>${formatResourceName(key)}</h4>
      <p>${resData[key].toLocaleString()}</p>
    `;
    gridEl.appendChild(card);
  });
}

// ✅ Load Buildings
async function loadVillageBuildings(villageId) {
  const listEl = document.getElementById('building-list');
  listEl.innerHTML = "<p>Loading buildings...</p>";

  const { data: buildings, error } = await supabase
    .from('village_buildings')
    .select('building_name, level')
    .eq('village_id', villageId)
    .order('building_name', { ascending: true });

  if (error) {
    console.error("❌ Error loading buildings:", error);
    listEl.innerHTML = "<p>Failed to load buildings.</p>";
    return;
  }

  listEl.innerHTML = "";

  if (buildings.length === 0) {
    listEl.innerHTML = "<p>No buildings constructed.</p>";
    return;
  }

  buildings.forEach(building => {
    const card = document.createElement('div');
    card.classList.add('building-card');
    card.innerHTML = `
      <h4>${building.building_name}</h4>
      <p>Level: ${building.level}</p>
    `;
    listEl.appendChild(card);
  });
}

// ✅ Load Modifiers
async function loadVillageModifiers(villageId) {
  const modEl = document.getElementById('modifier-list');
  if (!modEl) return;
  modEl.innerHTML = "<p>Loading modifiers...</p>";

  const { data: mods, error } = await supabase
    .from('village_modifiers')
    .select('*')
    .eq('village_id', villageId);

  if (error) {
    console.error('❌ Error loading modifiers:', error);
    modEl.innerHTML = '<p>Failed to load modifiers.</p>';
    return;
  }

  modEl.innerHTML = '';
  const now = Date.now();
  if (!mods || mods.length === 0) {
    modEl.innerHTML = '<p>No active modifiers.</p>';
    return;
  }

  mods.forEach(mod => {
    if (mod.expires_at && new Date(mod.expires_at).getTime() < now) return;
    const card = document.createElement('div');
    card.classList.add('modifier-card');
    card.innerHTML = `
      <h4>${mod.source}</h4>
      <p>Expires: ${mod.expires_at ? new Date(mod.expires_at).toLocaleDateString() : 'Never'}</p>
    `;
    modEl.appendChild(card);
  });
}

// ✅ Load Military
async function loadVillageMilitary(villageId) {
  const milEl = document.getElementById('military-stats');
  milEl.innerHTML = "<p>Loading military...</p>";

  const { data: military, error } = await supabase
    .from('village_military')
    .select('unit_name, quantity')
    .eq('village_id', villageId)
    .order('unit_name', { ascending: true });

  if (error) {
    console.error("❌ Error loading military:", error);
    milEl.innerHTML = "<p>Failed to load military.</p>";
    return;
  }

  milEl.innerHTML = "";

  if (military.length === 0) {
    milEl.innerHTML = "<p>No stationed troops.</p>";
    return;
  }

  military.forEach(unit => {
    const card = document.createElement('div');
    card.classList.add('military-card');
    card.innerHTML = `
      <h4>${unit.unit_name}</h4>
      <p>Quantity: ${unit.quantity}</p>
    `;
    milEl.appendChild(card);
  });
}

// ✅ Load Queue
async function loadVillageQueue(villageId) {
  const queueEl = document.getElementById('queue-list');
  queueEl.innerHTML = "<p>Loading queue...</p>";

  const { data: queue, error } = await supabase
    .from('village_queue')
    .select('*')
    .eq('village_id', villageId)
    .order('queue_ends_at', { ascending: true });

  if (error) {
    console.error("❌ Error loading queue:", error);
    queueEl.innerHTML = "<p>Failed to load queue.</p>";
    return;
  }

  queueEl.innerHTML = "";

  if (queue.length === 0) {
    queueEl.innerHTML = "<p>No active build or training queue.</p>";
    return;
  }

  queue.forEach(entry => {
    const card = document.createElement('div');
    card.classList.add('queue-card');
    card.innerHTML = `
      <h4>${entry.queue_type}: ${entry.item_name}</h4>
      <p>Ends: ${new Date(entry.queue_ends_at).toLocaleString()}</p>
    `;
    queueEl.appendChild(card);
  });
}

// ✅ Load Event Log
async function loadVillageEvents(villageId) {
  const logEl = document.getElementById('event-log');
  logEl.innerHTML = "<p>Loading events...</p>";

  const { data: events, error } = await supabase
    .from('village_events')
    .select('*')
    .eq('village_id', villageId)
    .order('event_time', { descending: true })
    .limit(10);

  if (error) {
    console.error("❌ Error loading event log:", error);
    logEl.innerHTML = "<p>Failed to load event log.</p>";
    return;
  }

  logEl.innerHTML = "";

  if (events.length === 0) {
    logEl.innerHTML = "<p>No recent events.</p>";
    return;
  }

  events.forEach(event => {
    const entry = document.createElement('div');
    entry.classList.add('event-entry');
    entry.innerHTML = `
      <p>[${new Date(event.event_time).toLocaleString()}] ${event.event_description}</p>
    `;
    logEl.appendChild(entry);
  });
}

// ✅ Helper: Format Resource Name
function formatResourceName(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

// ✅ Helper: Toast
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
