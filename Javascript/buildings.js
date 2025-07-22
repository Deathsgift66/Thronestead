// JS file: buildings.js
// Handles village and building management interactions on the buildings page.

import { escapeHTML } from './core_utils.js';

document.addEventListener('DOMContentLoaded', async () => {
  await loadVillages();
  setupEventListeners();
});

// Fetch and populate the village selector dropdown
async function loadVillages() {
  try {
    const res = await fetch('/api/kingdom/villages');
    const json = await res.json();
    const villages = json.villages || json;
    const select = document.getElementById('villageSelect');
    select.innerHTML = '';

    villages.forEach(village => {
      const option = document.createElement('option');
      option.value = village.village_id;
      option.textContent = village.village_name;
      select.appendChild(option);
    });

    if (villages.length > 0) {
      loadBuildings(villages[0].village_id);
    }

    select.addEventListener('change', e => {
      loadBuildings(e.target.value);
    });
  } catch (err) {
    console.error('Failed to load villages:', err);
    alert('Error loading villages. Try again later.');
  }
}

// Load buildings for a specific village
async function loadBuildings(villageId) {
  const tbody = document.getElementById('buildingsTableBody');
  tbody.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';
  try {
    const res = await fetch(`/api/buildings/village/${villageId}`);
    const json = await res.json();
    const buildings = json.buildings || json;
    tbody.innerHTML = '';

    buildings.forEach(building => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><img src="Assets/buildings/${building.icon}" alt="${building.name}" width="32" height="32" onerror="this.src='Assets/buildings/placeholder.png'"></td>
        <td>${building.name}</td>
        <td>${building.level}</td>
        <td>${building.status}</td>
        <td>
          <button class="info-btn" data-id="${building.id}">📘 Info</button>
          <button class="upgrade-btn" data-id="${building.id}" ${building.status == 'Upgrading' ? 'disabled' : ''}>⬆ Upgrade</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    attachRowActions();
  } catch (err) {
    console.error('Failed to load buildings:', err);
    tbody.innerHTML = '<tr><td colspan="5">Error loading buildings.</td></tr>';
    alert('Error loading buildings. Try again later.');
  }
}

// Attach modal and upgrade button logic
function attachRowActions() {
  document.querySelectorAll('.info-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      const buildingId = e.target.dataset.id;
      try {
        const res = await fetch(`/api/buildings/info/${buildingId}`);
        const data = await res.json();
        const info = data.building || data;

        document.getElementById('modalBuildingName').textContent = escapeHTML(info.building_name || info.name);
        document.getElementById('modalBuildingDesc').textContent = escapeHTML(info.description || '');
        document.getElementById('modalBuildCost').textContent = formatCost(info.upgrade_cost);

        document.getElementById('buildingModal').classList.remove('hidden');
      } catch (err) {
        console.error('Failed to fetch building info:', err);
        alert('Error fetching building info.');
      }
    });
  });

  document.querySelectorAll('.upgrade-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      const buildingId = e.target.dataset.id;
      const villageId = document.getElementById('villageSelect').value;
      try {
        const res = await fetch(`/api/buildings/upgrade`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            village_id: parseInt(villageId),
            building_id: parseInt(buildingId)
          })
        });
        const result = await res.json();
        alert(result.message || 'Upgrade started!');
        loadBuildings(document.getElementById('villageSelect').value);
      } catch (err) {
        console.error('Upgrade failed:', err);
        alert('Failed to start upgrade. Try again later.');
      }
    });
  });
}

// Format upgrade cost nicely for the modal
function formatCost(costObj) {
  if (!costObj) return '';
  return Object.entries(costObj)
    .map(([resource, amount]) => `${resource}: ${amount}`)
    .join('\n');
}

// Setup modal close button
function setupEventListeners() {
  const closeBtn = document.getElementById('buildingModalClose');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      document.getElementById('buildingModal').classList.add('hidden');
    });
  }
}
