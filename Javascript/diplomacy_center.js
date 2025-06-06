/*
Project Name: Kingmakers Rise Frontend
File Name: diplomacy_center.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Hardened Diplomacy Center — Diplomatic State Overview

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "login.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load
  await loadDiplomacyCenter();
});

// ✅ Load Diplomacy Center
async function loadDiplomacyCenter() {
  const container = document.querySelector(".content-container");

  container.innerHTML = "<p>Loading Diplomacy Center...</p>";

  try {
    // ✅ Fetch alliances
    const alliancesRes = await fetch("/api/diplomacy/alliances");
    const alliancesData = await alliancesRes.json();

    // ✅ Fetch treaties
    const treatiesRes = await fetch("/api/diplomacy/treaties");
    const treatiesData = await treatiesRes.json();

    // ✅ Fetch conflicts
    const conflictsRes = await fetch("/api/diplomacy/conflicts");
    const conflictsData = await conflictsRes.json();

    // ✅ Clear container
    container.innerHTML = "";

    // ✅ Render Alliances
    const alliancesSection = document.createElement("section");
    alliancesSection.classList.add("diplomacy-section");

    const alliancesHeader = document.createElement("h3");
    alliancesHeader.textContent = "🤝 Current Alliances";
    alliancesSection.appendChild(alliancesHeader);

    if (alliancesData.alliances && alliancesData.alliances.length > 0) {
      const alliancesList = document.createElement("ul");
      alliancesData.alliances.forEach(alliance => {
        const li = document.createElement("li");
        li.textContent = `${escapeHTML(alliance.name)} — ${escapeHTML(alliance.status || "Neutral")}`;
        alliancesList.appendChild(li);
      });
      alliancesSection.appendChild(alliancesList);
    } else {
      alliancesSection.innerHTML += "<p>No current alliances.</p>";
    }

    container.appendChild(alliancesSection);

    // ✅ Render Treaties
    const treatiesSection = document.createElement("section");
    treatiesSection.classList.add("diplomacy-section");

    const treatiesHeader = document.createElement("h3");
    treatiesHeader.textContent = "📜 Active Treaties";
    treatiesSection.appendChild(treatiesHeader);

    if (treatiesData.treaties && treatiesData.treaties.length > 0) {
      const treatiesList = document.createElement("ul");
      treatiesData.treaties.forEach(treaty => {
        const li = document.createElement("li");
        li.textContent = `${escapeHTML(treaty.partners || "Unknown parties")} — ${escapeHTML(treaty.type)} (${escapeHTML(treaty.status)})`;
        treatiesList.appendChild(li);
      });
      treatiesSection.appendChild(treatiesList);
    } else {
      treatiesSection.innerHTML += "<p>No active treaties.</p>";
    }

    container.appendChild(treatiesSection);

    // ✅ Render Conflicts
    const conflictsSection = document.createElement("section");
    conflictsSection.classList.add("diplomacy-section");

    const conflictsHeader = document.createElement("h3");
    conflictsHeader.textContent = "⚔️ Ongoing Conflicts";
    conflictsSection.appendChild(conflictsHeader);

    if (conflictsData.conflicts && conflictsData.conflicts.length > 0) {
      const conflictsList = document.createElement("ul");
      conflictsData.conflicts.forEach(conflict => {
        const li = document.createElement("li");
        li.textContent = `${escapeHTML(conflict.parties || "Unknown parties")} — ${escapeHTML(conflict.status || "Ongoing")} — Started: ${escapeHTML(conflict.started || "Unknown")}`;
        conflictsList.appendChild(li);
      });
      conflictsSection.appendChild(conflictsList);
    } else {
      conflictsSection.innerHTML += "<p>No ongoing conflicts.</p>";
    }

    container.appendChild(conflictsSection);

  } catch (err) {
    console.error("❌ Error loading Diplomacy Center:", err);
    container.innerHTML = "<p>Failed to load Diplomacy Center.</p>";
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
