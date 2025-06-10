/*
Project Name: Kingmakers Rise Frontend
File Name: overview.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Kingdom Overview — Summary + Resources + Military + Quests

import { supabase } from './supabaseClient.js';
import { loadPlayerProgressionFromStorage, fetchAndStorePlayerProgression } from './progressionGlobal.js';

let currentUser = null;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }
  currentUser = session.user;

  loadPlayerProgressionFromStorage();
  if (!window.playerProgression) {
    await fetchAndStorePlayerProgression(session.user.id);
  }

  // ✅ Initial load
  await loadOverview();
  // realtime updates to resources
  subscribeToResourceUpdates();
});

// ✅ Load Overview Data
async function loadOverview() {
  const summaryContainer = document.querySelector(".overview-summary");
  const resourcesContainer = document.getElementById("overview-resources");
  const militaryContainer = document.getElementById("overview-military");
  const questsContainer = document.getElementById("overview-quests");
  const modifiersContainer = document.getElementById("overview-modifiers");

  // Placeholders while loading
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

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();
    if (userError) throw userError;
    const kingdomId = userData.kingdom_id;

    const ovRes = await fetch('/api/overview', {
      headers: { 'X-User-ID': currentUser.id }
    });
    const data = await ovRes.json();

    // ✅ Summary Panel
    summaryContainer.innerHTML = `
      <p id="summary-region"></p>
      <p><strong>Castle Level:</strong> ${prog.castleLevel}</p>
      <p id="vip-level"></p>
      <p><strong>Max Villages:</strong> ${prog.maxVillages}</p>
      <p><strong>Nobles:</strong> ${prog.availableNobles} / ${prog.totalNobles}</p>
      <p><strong>Knights:</strong> ${prog.availableKnights} / ${prog.totalKnights}</p>
      <p><strong>Troop Slots:</strong> ${prog.troopSlots.used} / ${prog.troopSlots.used + prog.troopSlots.available}</p>
    `;

    const regionEl = document.getElementById('summary-region');
    try {
      const { data: krec } = await supabase
        .from('kingdoms')
        .select('region')
        .eq('user_id', currentUser.id)
        .single();
      let regionCode = krec?.region || 'Unspecified';
      let regionName = regionCode;
      if (regionCode) {
        const { data: rdata } = await supabase
          .from('region_catalogue')
          .select('region_name')
          .eq('region_code', regionCode)
          .single();
        regionName = rdata?.region_name || regionCode;
      }
      if (regionEl) regionEl.innerHTML = `<strong>Region:</strong> ${escapeHTML(regionName)}`;
    } catch (e) {
      if (regionEl) regionEl.textContent = 'Region: --';
    }

    // VIP Level
    try {
      const vipRes = await fetch('/api/kingdom/vip_status', {
        headers: { 'X-User-ID': currentUser.id }
      });
      const vipData = await vipRes.json();
      const vipEl = document.getElementById('vip-level');
      const lvl = vipData.vip_level || 0;
      if (vipEl) vipEl.innerHTML = `<strong>VIP:</strong> ${lvl}`;
    } catch (e) {
      const vipEl = document.getElementById('vip-level');
      if (vipEl) vipEl.textContent = 'VIP: --';
    }

    // ✅ Resources Panel
    resourcesContainer.innerHTML = "";
    if (data.resources && Object.keys(data.resources).length > 0) {
      const list = document.createElement("ul");
      for (const [resource, amount] of Object.entries(data.resources)) {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${escapeHTML(resource)}:</strong> ${amount}`;
        list.appendChild(li);
      }
      resourcesContainer.appendChild(list);
    } else {
      resourcesContainer.innerHTML = "<p>No resources found.</p>";
    }

    // ✅ Military Panel
    militaryContainer.innerHTML = ``;
  if (data.troops) {
      const p = document.createElement('p');
      p.innerHTML = `<strong>Total Troops:</strong> ${data.troops.total}`;
      const p2 = document.createElement('p');
      p2.innerHTML = `<strong>Slots Used:</strong> ${data.troops.slots.used} / ${data.troops.slots.base}`;
      militaryContainer.appendChild(p);
      militaryContainer.appendChild(p2);
  } else {
      militaryContainer.innerHTML = "<p>No military data found.</p>";
  }

    // ✅ Modifiers Panel
    if (modifiersContainer) {
      try {
        const res = await fetch('/api/progression/modifiers');
        const mods = await res.json();
        if (!res.ok) throw new Error('Failed');
        modifiersContainer.innerHTML = '';
        for (const [cat, vals] of Object.entries(mods)) {
          const h4 = document.createElement('h4');
          h4.textContent = cat.replace(/_/g, ' ');
          modifiersContainer.appendChild(h4);
          const ul = document.createElement('ul');
          for (const [k,v] of Object.entries(vals)) {
            const li = document.createElement('li');
            li.textContent = `${k}: ${v}`;
            ul.appendChild(li);
          }
          modifiersContainer.appendChild(ul);
        }
      } catch (e) {
        modifiersContainer.innerHTML = '<p>Failed to load modifiers.</p>';
      }
    }

    // ✅ Quests Panel (placeholder)
    questsContainer.innerHTML = "<p>No active quests.</p>";

  } catch (err) {
    console.error("❌ Error loading overview:", err);
    summaryContainer.innerHTML = "<p>Failed to load summary.</p>";
    resourcesContainer.innerHTML = "<p>Failed to load resources.</p>";
    militaryContainer.innerHTML = "<p>Failed to load military overview.</p>";
    questsContainer.innerHTML = "<p>Failed to load quests.</p>";
  }
}

// ✅ Basic HTML escape
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Subscribe to realtime resource updates
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
          .on(
            'postgres_changes',
            { event: '*', schema: 'public', table: 'kingdom_resources', filter: `kingdom_id=eq.${kid}` },
            (payload) => {
              if (payload.new) {
                updateResourceUI(payload.new);
              }
            }
          )
          .subscribe();
      });
  });
}

function updateResourceUI(row) {
  const container = document.getElementById('overview-resources');
  if (!container) return;
  container.innerHTML = '';
  const list = document.createElement('ul');
  for (const [k, v] of Object.entries(row)) {
    if (k === 'kingdom_id') continue;
    const li = document.createElement('li');
    li.innerHTML = `<strong>${escapeHTML(k)}:</strong> ${v}`;
    list.appendChild(li);
  }
  container.appendChild(list);
}
