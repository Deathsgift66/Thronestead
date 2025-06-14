// Project Name: Kingmakers Rise©
// File Name: buildings.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';

// Keys to check for cost display
const RESOURCE_KEYS = [
  'wood', 'stone', 'iron_ore', 'gold', 'gems', 'food', 'coal',
  'livestock', 'clay', 'flax', 'tools', 'wood_planks', 'refined_stone',
  'iron_ingots', 'charcoal', 'leather', 'arrows', 'swords', 'axes',
  'shields', 'armour', 'wagon', 'siege_weapons', 'jewelry', 'spear',
  'horses', 'pitchforks', 'wood_cost', 'stone_cost', 'iron_cost',
  'gold_cost', 'wood_plan_cost', 'iron_ingot_cost'
];

let currentVillage = null;
let timerHandle = null;
let modal, modalName, modalDesc, modalCost;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return window.location.href = 'login.html';

  // Cache modal references
  modal = document.getElementById('buildingModal');
  modalName = document.getElementById('modalBuildingName');
  modalDesc = document.getElementById('modalBuildingDesc');
  modalCost = document.getElementById('modalBuildCost');

  // Modal close event
  document.getElementById('buildingModalClose')?.addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  await loadVillages();
});

// ========== Load Villages and Populate Dropdown ==========
async function loadVillages() {
  const select = document.getElementById('villageSelect');
  const { data: { user } } = await supabase.auth.getUser();
  const res = await fetch('/api/kingdom/villages', { headers: { 'X-User-ID': user.id } });
  const { villages = [] } = await res.json();

  select.innerHTML = '';
  villages.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.village_id;
    opt.textContent = v.village_name;
    select.appendChild(opt);
  });

  if (!villages.length) return;
  currentVillage = villages[0].village_id;
  select.value = currentVillage;

  select.addEventListener('change', () => {
    currentVillage = parseInt(select.value, 10);
    loadBuildings();
  });

  await loadBuildings();
}

// ========== Load Buildings for Selected Village ==========
async function loadBuildings() {
  if (!currentVillage) return;
  if (timerHandle) clearInterval(timerHandle);

  const tbody = document.getElementById('buildingsTableBody');
  tbody.innerHTML = `<tr><td colspan="5">Loading...</td></tr>`;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch(`/api/buildings/village/${currentVillage}`, {
      headers: { 'X-User-ID': user.id }
    });
    const { buildings = [] } = await res.json();
    tbody.innerHTML = '';

    buildings.forEach(b => {
      const row = document.createElement('tr');
      row.dataset.buildingId = b.building_id;
      row.classList.add('building-row');
      row.addEventListener('click', () => showBuildingInfo(b.building_id));

      const status = b.is_under_construction
        ? `<div class="progress-bar">
             <div class="progress-bar-fill" data-start="${b.construction_started_at}" data-end="${b.construction_ends_at}"></div>
           </div>
           <span class="timer" data-start="${b.construction_started_at}" data-end="${b.construction_ends_at}"></span>`
        : 'Ready';

      let actions = '';
      if (b.is_under_construction) {
        actions = `<button class="action-btn cancel-btn" data-building-id="${b.building_id}">Cancel</button>`;
      } else {
        const label = b.level === 0 ? 'Build' : 'Upgrade';
        actions = `<button class="action-btn build-btn" data-building-id="${b.building_id}">${label}</button>`;
        if (b.level > 0) {
          actions += ` <button class="action-btn reset-btn" data-building-id="${b.building_id}">Reset</button>`;
        }
      }

      row.innerHTML = `
        <td><img src="Assets/buildings/${b.building_id}.png" class="building-icon" onerror="this.src='Assets/buildings/building_default.png'" alt="${b.building_name}"></td>
        <td>${escapeHTML(b.building_name)}</td>
        <td>${b.level}</td>
        <td>${status}</td>
        <td>${actions}</td>
      `;
      tbody.appendChild(row);
    });

    bindButtons();
    updateTimers();
    timerHandle = setInterval(updateTimers, 1000);
  } catch (err) {
    console.error('Error loading buildings:', err);
    tbody.innerHTML = `<tr><td colspan="5">Failed to load buildings.</td></tr>`;
  }
}

// ========== Button Event Binding ==========
function bindButtons() {
  document.querySelectorAll('.build-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.stopPropagation();
      await handleBuildOrUpgrade(btn);
    });
  });

  document.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.stopPropagation();
      if (confirm('Cancel construction?')) await handleCancel(btn);
    });
  });

  document.querySelectorAll('.reset-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.stopPropagation();
      if (confirm('Reset building level to 0?')) await handleReset(btn);
    });
  });
}

async function handleBuildOrUpgrade(btn) {
  const buildingId = parseInt(btn.dataset.buildingId, 10);
  const action = btn.textContent.toLowerCase() === 'build' ? 'construct' : 'upgrade';
  const { data: { user } } = await supabase.auth.getUser();

  const res = await fetch(`/api/buildings/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
    body: JSON.stringify({ village_id: currentVillage, building_id: buildingId })
  });
  const result = await res.json();
  alert(result.message);
  await loadBuildings();
}

async function handleCancel(btn) {
  const buildingId = parseInt(btn.dataset.buildingId, 10);
  const { data: { user } } = await supabase.auth.getUser();

  const res = await fetch('/api/buildings/cancel', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
    body: JSON.stringify({ village_id: currentVillage, building_id: buildingId })
  });
  const result = await res.json();
  alert(result.message);
  await loadBuildings();
}

async function handleReset(btn) {
  const buildingId = parseInt(btn.dataset.buildingId, 10);
  const { data: { user } } = await supabase.auth.getUser();

  const res = await fetch('/api/buildings/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
    body: JSON.stringify({ village_id: currentVillage, building_id: buildingId })
  });
  const result = await res.json();
  alert(result.message);
  await loadBuildings();
}

// ========== Update Progress Bars ==========
function updateTimers() {
  const now = Date.now();

  document.querySelectorAll('.progress-bar-fill').forEach(bar => {
    const start = new Date(bar.dataset.start).getTime();
    const end = new Date(bar.dataset.end).getTime();
    const total = end - start;
    const elapsed = Math.max(0, now - start);
    const pct = Math.min(100, (elapsed / total) * 100);
    bar.style.width = `${pct}%`;

    const timer = bar.closest('td').querySelector('.timer');
    if (timer) {
      const remaining = Math.max(0, end - now);
      timer.textContent = remaining > 0 ? `${Math.ceil(remaining / 1000)}s` : 'Done';
    }
  });
}

// ========== Modal: Show Building Info ==========
async function showBuildingInfo(buildingId) {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch(`/api/buildings/info/${buildingId}`, {
      headers: { 'X-User-ID': user.id }
    });
    if (!res.ok) throw new Error('Fetch failed');
    const { building } = await res.json();

    modalName.textContent = building.building_name;
    modalDesc.textContent = building.description || '';
    modalCost.textContent = formatCostFromColumns(building);
    modal.classList.remove('hidden');
  } catch (err) {
    console.error('Error fetching building info:', err);
    alert('Failed to load building details.');
  }
}

// ========== Helpers ==========

function formatCostFromColumns(obj) {
  return RESOURCE_KEYS
    .filter(key => typeof obj[key] === 'number' && obj[key] > 0)
    .map(key => `${obj[key]} ${escapeHTML(key.replace(/_cost$/, ''))}`)
    .join(', ') || 'N/A';
}
