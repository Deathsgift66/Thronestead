/*
Project Name: Kingmakers Rise Frontend
File Name: buildings.js
Updated: 2025-06-03 by Codex
*/
// Buildings Management with real-time progress

import { supabase } from './supabaseClient.js';

let currentVillage = null;
let timerHandle = null;
let modal, modalName, modalDesc, modalCost;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  modal = document.getElementById('buildingModal');
  modalName = document.getElementById('modalBuildingName');
  modalDesc = document.getElementById('modalBuildingDesc');
  modalCost = document.getElementById('modalBuildCost');
  document.getElementById('buildingModalClose').addEventListener('click', () => {
    modal.classList.add('hidden');
  });
  await loadVillages();
});

async function loadVillages() {
  const select = document.getElementById('villageSelect');
  const { data: { user } } = await supabase.auth.getUser();
  const res = await fetch('/api/kingdom/villages', {
    headers: { 'X-User-ID': user.id }
  });
  const data = await res.json();
  const villages = data.villages || [];
  select.innerHTML = '';
  villages.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.village_id;
    opt.textContent = v.village_name;
    select.appendChild(opt);
  });
  if (villages.length) {
    currentVillage = villages[0].village_id;
    select.value = currentVillage;
    select.addEventListener('change', () => {
      currentVillage = parseInt(select.value, 10);
      loadBuildings();
    });
    await loadBuildings();
  }
}

async function loadBuildings() {
  if (timerHandle) clearInterval(timerHandle);
  const tbody = document.getElementById('buildingsTableBody');
  tbody.innerHTML = `<tr><td colspan="5">Loading...</td></tr>`;
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch(`/api/buildings/village/${currentVillage}`, {
      headers: { 'X-User-ID': user.id }
    });
    const json = await res.json();
    const buildings = json.buildings || [];
    tbody.innerHTML = '';
    buildings.forEach(b => {
      const row = document.createElement('tr');
      row.dataset.buildingId = b.building_id;
      row.classList.add('building-row');
      row.addEventListener('click', () => showBuildingInfo(b.building_id));
      const statusCell = document.createElement('td');
      let statusHTML = 'Ready';
      if (b.is_under_construction) {
        statusHTML = `
          <div class="progress-bar">
            <div class="progress-bar-fill" data-start="${b.construction_started_at}" data-end="${b.construction_ends_at}"></div>
          </div>
          <span class="timer" data-start="${b.construction_started_at}" data-end="${b.construction_ends_at}"></span>
        `;
      }
      statusCell.innerHTML = statusHTML;
      const btnLabel = b.level === 0 ? 'Build' : 'Upgrade';
      let actionHTML = '';
      if (b.is_under_construction) {
        actionHTML = `<button class="action-btn cancel-btn" data-building-id="${b.building_id}">Cancel</button>`;
      } else {
        actionHTML = `<button class="action-btn build-btn" data-building-id="${b.building_id}">${btnLabel}</button>`;
        if (b.level > 0) {
          actionHTML += ` <button class="action-btn reset-btn" data-building-id="${b.building_id}">Reset</button>`;
        }
      }
      row.innerHTML = `
        <td><img src="Assets/buildings/${b.building_id}.png" class="building-icon" onerror="this.src='Assets/buildings/building_default.png'" alt="${b.building_name}"></td>
        <td>${escapeHTML(b.building_name)}</td>
        <td>${b.level}</td>
      `;
      row.appendChild(statusCell);
      row.innerHTML += `<td>${actionHTML}</td>`;
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

function bindButtons() {
  document.querySelectorAll('.build-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const buildingId = parseInt(btn.dataset['buildingId'], 10);
      const action = btn.textContent.toLowerCase() === 'build' ? 'construct' : 'upgrade';
      try {
        const { data: { user } } = await supabase.auth.getUser();
        const res = await fetch(`/api/buildings/${action}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
          body: JSON.stringify({ village_id: currentVillage, building_id: buildingId })
        });
        const result = await res.json();
        alert(result.message);
        await loadBuildings();
      } catch (err) {
        console.error('Action failed:', err);
        alert('Action failed');
      }
    });
  });

  document.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const buildingId = parseInt(btn.dataset['buildingId'], 10);
      if (!confirm('Cancel construction?')) return;
      try {
        const { data: { user } } = await supabase.auth.getUser();
        const res = await fetch('/api/buildings/cancel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
          body: JSON.stringify({ village_id: currentVillage, building_id: buildingId })
        });
        const result = await res.json();
        alert(result.message);
        await loadBuildings();
      } catch (err) {
        console.error('Cancel failed:', err);
        alert('Action failed');
      }
    });
  });

  document.querySelectorAll('.reset-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const buildingId = parseInt(btn.dataset['buildingId'], 10);
      if (!confirm('Reset building level to 0?')) return;
      try {
        const { data: { user } } = await supabase.auth.getUser();
        const res = await fetch('/api/buildings/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
          body: JSON.stringify({ village_id: currentVillage, building_id: buildingId })
        });
        const result = await res.json();
        alert(result.message);
        await loadBuildings();
      } catch (err) {
        console.error('Reset failed:', err);
        alert('Action failed');
      }
    });
  });
}

function updateTimers() {
  const now = Date.now();
  document.querySelectorAll('.progress-bar-fill').forEach(bar => {
    const start = new Date(bar.dataset['start']).getTime();
    const end = new Date(bar.dataset['end']).getTime();
    const total = end - start;
    const remaining = end - now;
    const pct = Math.min(100, Math.max(0, ((total - remaining) / total) * 100));
    bar.style.width = pct + '%';
    const timer = bar.parentElement.nextElementSibling;
    if (timer) {
      timer.textContent = remaining > 0 ? Math.ceil(remaining / 1000) + 's' : 'Done';
    }
  });
}

async function showBuildingInfo(bid) {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch(`/api/buildings/info/${bid}`, {
      headers: { 'X-User-ID': user.id }
    });
    if (!res.ok) throw new Error('Failed');
    const { building } = await res.json();
    modalName.textContent = building.building_name;
    modalDesc.textContent = building.description || '';
    modalCost.textContent = JSON.stringify(building.build_cost, null, 2);
    modal.classList.remove('hidden');
  } catch (err) {
    console.error('Failed to load building info', err);
  }
}

function escapeHTML(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
