// Project Name: Thronestead©
// File Name: overview.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// Kingdom Overview — Summary + Resources + Military + Quests + Modifiers
import { escapeHTML } from './utils.js';
import { fetchJson, authFetchJson } from './fetchJson.js';

import { supabase } from '../supabaseClient.js';
import { loadPlayerProgressionFromStorage, fetchAndStorePlayerProgression } from './progressionGlobal.js';

// Currently authenticated user and session
let currentUser = null;
let currentSession = null;

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return window.location.href = "login.html";
  currentUser = session.user;
  currentSession = session;

  loadPlayerProgressionFromStorage();
  if (!window.playerProgression) await fetchAndStorePlayerProgression(currentUser.id);

  await loadOverview();
  subscribeToResourceUpdates();
});

async function loadOverview() {
  const summaryContainer = document.querySelector(".overview-summary");
  const resourcesContainer = document.getElementById("overview-resources");
  const militaryContainer = document.getElementById("overview-military");
  const questsContainer = document.getElementById("overview-quests");
  const modifiersContainer = document.getElementById("overview-modifiers");

  summaryContainer.innerHTML = "<p>Loading summary...</p>";
  resourcesContainer.innerHTML = "<p>Loading resources...</p>";
  militaryContainer.innerHTML = "<p>Loading military overview...</p>";
  questsContainer.innerHTML = "<p>Loading quests...</p>";
  if (modifiersContainer) modifiersContainer.innerHTML = "<p>Loading modifiers...</p>";

  try {
    const prog = window.playerProgression;
    const data = await authFetchJson('/api/overview', currentSession);

    summaryContainer.innerHTML = `
      <p id="summary-region"></p>
      <p><strong>Castle Level:</strong> ${prog.castleLevel}</p>
      <p id="vip-level"></p>
      <p><strong>Max Villages:</strong> ${prog.maxVillages}</p>
      <p><strong>Nobles:</strong> ${prog.availableNobles} / ${prog.totalNobles}</p>
      <p><strong>Knights:</strong> ${prog.availableKnights} / ${prog.totalKnights}</p>
      <p><strong>Troop Slots:</strong> ${prog.troopSlots.used} / ${prog.troopSlots.total}</p>
    `;

    try {
      const { data: krec } = await supabase
        .from('kingdoms')
        .select('region')
        .eq('user_id', currentUser.id)
        .single();
      const regionCode = krec?.region || 'Unspecified';
      let regionName = regionCode;
      if (regionCode) {
        const { data: rdata } = await supabase
          .from('region_catalogue')
          .select('region_name')
          .eq('region_code', regionCode)
          .single();
        regionName = rdata?.region_name || regionCode;
      }
      document.getElementById('summary-region').innerHTML = `<strong>Region:</strong> ${escapeHTML(regionName)}`;
    } catch {
      document.getElementById('summary-region').textContent = 'Region: --';
    }

    try {
      const vipData = await authFetchJson('/api/kingdom/vip_status', currentSession);
      document.getElementById('vip-level').innerHTML = `<strong>VIP:</strong> ${vipData.vip_level || 0}`;
    } catch {
      document.getElementById('vip-level').textContent = 'VIP: --';
    }

    // Resources
    renderResourceList(data.resources, resourcesContainer);

    // Military
    militaryContainer.innerHTML = "";
    if (data.troops) {
      militaryContainer.innerHTML = `
        <p><strong>Total Troops:</strong> ${data.troops.total}</p>
        <p><strong>Slots Used:</strong> ${data.troops.slots.used} / ${data.troops.slots.base}</p>
      `;
    } else {
      militaryContainer.innerHTML = "<p>No military data found.</p>";
    }

    // Modifiers
    if (modifiersContainer) {
      try {
        const mods = await fetchJson('/api/progression/modifiers');
        modifiersContainer.innerHTML = '';
        for (const [cat, vals] of Object.entries(mods)) {
          const h4 = document.createElement('h4');
          h4.textContent = cat.replace(/_/g, ' ');
          const ul = document.createElement('ul');
          for (const [k, v] of Object.entries(vals)) {
            const li = document.createElement('li');
            li.textContent = `${k}: ${v}`;
            ul.appendChild(li);
          }
          modifiersContainer.appendChild(h4);
          modifiersContainer.appendChild(ul);
        }
      } catch {
        modifiersContainer.innerHTML = '<p>Failed to load modifiers.</p>';
      }
    }

    questsContainer.innerHTML = "<p>No active quests.</p>";
  } catch (err) {
    console.error("❌ Overview load error:", err);
    summaryContainer.innerHTML = "<p>Failed to load summary.</p>";
    resourcesContainer.innerHTML = "<p>Failed to load resources.</p>";
    militaryContainer.innerHTML = "<p>Failed to load military.</p>";
    questsContainer.innerHTML = "<p>Failed to load quests.</p>";
  }
}

// Live update for kingdom resources
async function subscribeToResourceUpdates() {
  const { data } = await supabase.auth.getUser();
  const uid = data?.user?.id;
  if (!uid) return;
  const { data: kidRow } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', uid)
    .single();
  const kid = kidRow?.kingdom_id;
  if (!kid) return;
  supabase
    .channel('kr-overview-' + kid)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'kingdom_resources',
      filter: `kingdom_id=eq.${kid}`
    }, payload => {
      if (payload.new) renderResourceList(payload.new, document.getElementById('overview-resources'));
    })
    .subscribe();
}

/**
 * Render a list of resources into a container.
 * @param {Object} resources Resource name/value pairs
 * @param {HTMLElement} container Target element
 */
function renderResourceList(resources, container) {
  if (!container) return;
  container.innerHTML = '';
  if (!resources || !Object.keys(resources).length) {
    container.innerHTML = '<p>No resources found.</p>';
    return;
  }
  const ul = document.createElement('ul');
  for (const [k, v] of Object.entries(resources)) {
    if (k === 'kingdom_id') continue;
    const li = document.createElement('li');
    li.innerHTML = `<strong>${escapeHTML(k)}:</strong> ${v}`;
    ul.appendChild(li);
  }
  container.appendChild(ul);
}
