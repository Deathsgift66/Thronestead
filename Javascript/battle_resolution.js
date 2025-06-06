/*
Project Name: Kingmakers Rise Frontend
File Name: battle_resolution.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Hardened Battle Resolution Page

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
  await loadBattleResolution();
});

// ✅ Load Battle Resolution
async function loadBattleResolution() {
  const statusText = document.getElementById("battle-status");
  const winnerText = document.getElementById("winner-name");
  const lossesSection = document.getElementById("losses");
  const rewardsSection = document.getElementById("rewards");
  const combatLogList = document.getElementById("combat-log-list");

  // Initial loading state
  statusText.textContent = "";
  winnerText.textContent = "";
  lossesSection.innerHTML = "<p>Loading losses...</p>";
  rewardsSection.innerHTML = "<p>Loading rewards...</p>";
  combatLogList.innerHTML = "<li>Loading combat log...</li>";

  try {
    const res = await fetch("/api/battle-resolution");
    const data = await res.json();

    // Outcome
    statusText.textContent = data.outcome?.status || "Unknown";
    winnerText.textContent = data.outcome?.winner || "Unknown";

    // Losses
    lossesSection.innerHTML = "";
    if (data.losses && Object.keys(data.losses).length > 0) {
      const list = document.createElement("ul");
      Object.entries(data.losses).forEach(([unit, count]) => {
        const li = document.createElement("li");
        li.textContent = `${unit}: ${count}`;
        list.appendChild(li);
      });
      lossesSection.appendChild(list);
    } else {
      lossesSection.innerHTML = "<p>No losses recorded.</p>";
    }

    // Rewards
    rewardsSection.innerHTML = "";
    if (data.rewards && Array.isArray(data.rewards) && data.rewards.length > 0) {
      const list = document.createElement("ul");
      data.rewards.forEach(reward => {
        const li = document.createElement("li");
        li.textContent = reward;
        list.appendChild(li);
      });
      rewardsSection.appendChild(list);
    } else if (typeof data.rewards === "string" && data.rewards.trim() !== "") {
      rewardsSection.innerHTML = `<p>${escapeHTML(data.rewards)}</p>`;
    } else {
      rewardsSection.innerHTML = "<p>No rewards from this battle.</p>";
    }

    // Combat log
    combatLogList.innerHTML = "";
    if (data.combat_log && data.combat_log.length > 0) {
      data.combat_log.forEach(event => {
        const li = document.createElement("li");
        li.textContent = event;
        combatLogList.appendChild(li);
      });
    } else {
      combatLogList.innerHTML = "<li>No combat events recorded.</li>";
    }

  } catch (err) {
    console.error("❌ Error loading battle resolution:", err);
    statusText.textContent = "Error loading.";
    winnerText.textContent = "";
    lossesSection.innerHTML = "<p>Failed to load losses.</p>";
    rewardsSection.innerHTML = "<p>Failed to load rewards.</p>";
    combatLogList.innerHTML = "<li>Failed to load combat log.</li>";
  }
}

// ✅ Basic HTML escape (for rewards string)
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
