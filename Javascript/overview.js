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
});

// ✅ Load Overview Data
async function loadOverview() {
  const summaryContainer = document.querySelector(".overview-summary");
  const resourcesContainer = document.getElementById("overview-resources");
  const militaryContainer = document.getElementById("overview-military");
  const questsContainer = document.getElementById("overview-quests");

  // Placeholders while loading
  summaryContainer.innerHTML = "<p>Loading summary...</p>";
  resourcesContainer.innerHTML = "<p>Loading resources...</p>";
  militaryContainer.innerHTML = "<p>Loading military overview...</p>";
  questsContainer.innerHTML = "<p>Loading quests...</p>";

  try {
    const [kingdomRes, prog] = await Promise.all([
      fetch('/api/kingdom/summary'),
      Promise.resolve(window.playerProgression)
    ]);
    const data = await kingdomRes.json();

    // ✅ Summary Panel
    summaryContainer.innerHTML = `
      <p id="summary-region"></p>
      <p><strong>Castle Level:</strong> ${prog.castleLevel}</p>
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
      let regionName = krec?.region || 'Unspecified';
      if (regionName) {
        const { data: rdata } = await supabase
          .from('region_catalogue')
          .select('name')
          .eq('region_code', regionName)
          .single();
        regionName = rdata?.name || regionName;
      }
      if (regionEl) regionEl.innerHTML = `<strong>Region:</strong> ${escapeHTML(regionName)}`;
    } catch (e) {
      if (regionEl) regionEl.textContent = 'Region: --';
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
