// Project Name: Kingmakers Rise©
// File Name: overview.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// Kingdom Overview — Summary + Resources + Military + Quests + Modifiers
import { escapeHTML } from './utils.js';

import { supabase } from './supabaseClient.js';
import { loadPlayerProgressionFromStorage, fetchAndStorePlayerProgression } from './progressionGlobal.js';

let currentUser = null;

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return window.location.href = "login.html";
  currentUser = session.user;

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
    const [{ data: { user } }, prog] = await Promise.all([
      supabase.auth.getUser(),
      Promise.resolve(window.playerProgression)
    ]);

    const { data: userData } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();
    const kingdomId = userData.kingdom_id;

    const ovRes = await fetch('/api/overview', {
      headers: { 'X-User-ID': currentUser.id }
    });
    const data = await ovRes.json();

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
      const vipRes = await fetch('/api/kingdom/vip_status', {
        headers: { 'X-User-ID': currentUser.id }
      });
      const vipData = await vipRes.json();
      document.getElementById('vip-level').innerHTML = `<strong>VIP:</strong> ${vipData.vip_level || 0}`;
    } catch {
      document.getElementById('vip-level').textContent = 'VIP: --';
    }

    // Resources
    resourcesContainer.innerHTML = "";
    if (data.resources && Object.keys(data.resources).length) {
      const ul = document.createElement("ul");
      for (const [key, val] of Object.entries(data.resources)) {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${escapeHTML(key)}:</strong> ${val}`;
        ul.appendChild(li);
      }
      resourcesContainer.appendChild(ul);
    } else {
      resourcesContainer.innerHTML = "<p>No resources found.</p>";
    }

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
        const res = await fetch('/api/progression/modifiers');
        const mods = await res.json();
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

// Escape dangerous HTML

// Live update for kingdom resources
function subscribeToResourceUpdates() {
  supabase.auth.getUser().then(({ data }) => {
    const uid = data?.user?.id;
    if (!uid) return;
    supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', uid)
      .single()
      .then(({ data }) => {
        const kid = data?.kingdom_id;
        if (!kid) return;
        supabase
          .channel('kr-overview-' + kid)
          .on('postgres_changes', {
            event: '*',
            schema: 'public',
            table: 'kingdom_resources',
            filter: `kingdom_id=eq.${kid}`
          }, payload => {
            if (payload.new) updateResourceUI(payload.new);
          })
          .subscribe();
      });
  });
}

function updateResourceUI(row) {
  const container = document.getElementById('overview-resources');
  if (!container) return;
  container.innerHTML = '';
  const ul = document.createElement('ul');
  for (const [k, v] of Object.entries(row)) {
    if (k === 'kingdom_id') continue;
    const li = document.createElement('li');
    li.innerHTML = `<strong>${escapeHTML(k)}:</strong> ${v}`;
    ul.appendChild(li);
  }
  container.appendChild(ul);
}
