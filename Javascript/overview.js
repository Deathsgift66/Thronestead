/*
Project Name: Kingmakers Rise Frontend
File Name: overview.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Kingdom Overview — Summary + Resources + Military + Quests

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
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
    const res = await fetch("/api/kingdom/overview");
    const data = await res.json();

    // ✅ Summary Panel
    summaryContainer.innerHTML = `
      <p><strong>Kingdom:</strong> ${escapeHTML(data.kingdom_name)}</p>
      <p><strong>Owner:</strong> ${escapeHTML(data.owner_name)}</p>
      <p><strong>VIP Tier:</strong> ${escapeHTML(data.vip_tier)}</p>
      <p><strong>Relationship Status:</strong> ${escapeHTML(data.relationship_status)}</p>
    `;

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
    militaryContainer.innerHTML = "";
    if (data.military_summary && Object.keys(data.military_summary).length > 0) {
      const list = document.createElement("ul");
      for (const [unit, count] of Object.entries(data.military_summary)) {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${escapeHTML(unit)}:</strong> ${count}`;
        list.appendChild(li);
      }
      militaryContainer.appendChild(list);
    } else {
      militaryContainer.innerHTML = "<p>No military data found.</p>";
    }

    // ✅ Quests Panel
    questsContainer.innerHTML = "";
    if (data.quests && data.quests.length > 0) {
      data.quests.forEach(quest => {
        const card = document.createElement("div");
        card.classList.add("quest-card");

        card.innerHTML = `
          <h4>${escapeHTML(quest.title)}</h4>
          <p>Status: ${escapeHTML(quest.status)}</p>
          <p>Progress: ${quest.progress}%</p>
        `;

        questsContainer.appendChild(card);
      });
    } else {
      questsContainer.innerHTML = "<p>No active quests.</p>";
    }

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
