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

    const { data: resRow, error: resErr } = await supabase
      .from('kingdom_resources')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .single();
    if (resErr) throw resErr;

    const { data: slotRow, error: slotErr } = await supabase
      .from('kingdom_troop_slots')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .single();
    if (slotErr) throw slotErr;

    const { data: troopsData, error: troopsErr } = await supabase
      .from('kingdom_troops')
      .select('quantity')
      .eq('kingdom_id', kingdomId);
    if (troopsErr) throw troopsErr;

    const totalTroops = troopsData.reduce((sum, r) => sum + (r.quantity || 0), 0);
    const baseSlots =
      (slotRow.base_slots || 0) +
      (slotRow.castle_bonus_slots || 0) +
      (slotRow.noble_bonus_slots || 0) +
      (slotRow.knight_bonus_slots || 0);
    const usedSlots = slotRow.used_slots || 0;

    const data = {
      resources: Object.fromEntries(
        Object.entries(resRow || {}).filter(([k]) => k !== 'kingdom_id')
      ),
      troops: {
        total: totalTroops,
        slots: {
          base: baseSlots,
          used: usedSlots,
          available: Math.max(0, baseSlots - usedSlots)
        }
      }
    };

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
