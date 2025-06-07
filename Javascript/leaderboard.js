/*
Project Name: Kingmakers Rise Frontend
File Name: leaderboard.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Full dynamic Leaderboard — Multi-tab + Alliance Apply

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Setup tabs
  setupTabs();

  // ✅ Load default tab (Top Kingdoms)
  await loadLeaderboard("kingdoms");
});

// ✅ Setup Tabs
function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab-button");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const target = btn.getAttribute("data-tab");

      // Activate clicked tab
      tabButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      // Load corresponding leaderboard
      await loadLeaderboard(target);
    });
  });
}

// ✅ Load Leaderboard
async function loadLeaderboard(type) {
  const tbody = document.getElementById("leaderboard-body");

  tbody.innerHTML = `
    <tr><td colspan="5">Loading leaderboard...</td></tr>
  `;

  try {
    const res = await fetch(`/api/leaderboard/${type}`);
    const data = await res.json();

    tbody.innerHTML = "";

    if (!data.entries || data.entries.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="5">No results available.</td></tr>
      `;
      return;
    }

    data.entries.forEach((entry, index) => {
      const row = document.createElement("tr");

      // Build row based on tab type
      if (type === "kingdoms") {
        row.innerHTML = `
          <td>${index + 1}</td>
          <td>${escapeHTML(entry.kingdom_name)}</td>
          <td>${escapeHTML(entry.ruler_name)}</td>
          <td>${entry.power_score}</td>
          <td>${entry.economy_score}</td>
        `;
      } else if (type === "alliances") {
        row.innerHTML = `
          <td>${index + 1}</td>
          <td>${escapeHTML(entry.alliance_name)}</td>
          <td>${entry.member_count}</td>
          <td>${entry.total_power}</td>
          <td>
            <button class="action-btn apply-btn" data-alliance-id="${entry.alliance_id}" data-alliance-name="${escapeHTML(entry.alliance_name)}">Apply</button>
          </td>
        `;
      } else if (type === "wars") {
        row.innerHTML = `
          <td>${index + 1}</td>
          <td>${escapeHTML(entry.kingdom_name)}</td>
          <td>${escapeHTML(entry.ruler_name)}</td>
          <td>${entry.battles_won}</td>
          <td>${entry.battles_lost}</td>
        `;
      } else if (type === "economy") {
        row.innerHTML = `
          <td>${index + 1}</td>
          <td>${escapeHTML(entry.kingdom_name)}</td>
          <td>${escapeHTML(entry.ruler_name)}</td>
          <td>${entry.total_trade_value}</td>
          <td>${entry.market_share}%</td>
        `;
      }

      tbody.appendChild(row);
    });

    // ✅ Bind Apply buttons (if Alliances tab)
    if (type === "alliances") {
      document.querySelectorAll(".apply-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const allianceId = btn.dataset.allianceId;
          const allianceName = btn.dataset.allianceName;
          openApplyModal(allianceId, allianceName);
        });
      });
    }

  } catch (err) {
    console.error(`❌ Error loading ${type} leaderboard:`, err);
    tbody.innerHTML = `
      <tr><td colspan="5">Failed to load leaderboard.</td></tr>
    `;
  }
}

// ✅ Open Apply Modal
function openApplyModal(allianceId, allianceName) {
  const modal = document.getElementById("apply-modal");
  const modalContent = modal.querySelector(".modal-content");

  // Populate modal content
  modalContent.innerHTML = `
    <h3>Apply to ${escapeHTML(allianceName)}</h3>
    <textarea id="application-message" placeholder="Write your application message..."></textarea>
    <br>
    <button class="action-btn" id="submit-application">Submit Application</button>
    <button class="action-btn" id="close-application">Cancel</button>
  `;

  // Show modal
  modal.classList.remove("hidden");

  // ✅ Bind Submit
  document.getElementById("submit-application").addEventListener("click", async () => {
    const message = document.getElementById("application-message").value.trim();

    if (!message) {
      alert("Please enter a message.");
      return;
    }

    try {
      const res = await fetch("/api/alliances/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alliance_id: allianceId,
          message
        })
      });

      const result = await res.json();

      if (!res.ok) {
        throw new Error(result.error || "Application failed.");
      }

      alert(result.message || "Application submitted!");
      modal.classList.add("hidden");

    } catch (err) {
      console.error("❌ Error submitting application:", err);
      alert("Application failed.");
    }
  });

  // ✅ Bind Cancel
  document.getElementById("close-application").addEventListener("click", () => {
    modal.classList.add("hidden");
  });
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
