// Project Name: Kingmakers Rise©
// File Name: leaderboard.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';
import { setupTabs } from './components/tabControl.js';

let currentTab = "kingdoms";

const headers = {
  kingdoms: ["Rank", "Kingdom", "Ruler", "Power", "Economy"],
  alliances: ["Rank", "Alliance", "Military", "Economy", "Diplomacy", "Wins", "Losses", "Prestige", "Apply"],
  wars: ["Rank", "Kingdom", "Ruler", "Wins", "Losses"],
  economy: ["Rank", "Kingdom", "Ruler", "Trade", "Market %"]
};

// 🔐 User session + leaderboard loader
document.addEventListener("DOMContentLoaded", async () => {
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  setupTabs({ onShow: id => { currentTab = id; loadLeaderboard(id); } });
  await loadLeaderboard(currentTab);

  setInterval(() => {
    loadLeaderboard(currentTab);
  }, 30000);
});

// 🧭 Tab switch logic for leaderboard page

// 📊 Load leaderboard by tab type
async function loadLeaderboard(type) {
  const tbody = document.getElementById("leaderboard-body");
  const headerRow = document.getElementById("leaderboard-headers");
  const cols = headers[type]?.length || 5;

  tbody.innerHTML = `<tr><td colspan="${cols}">Loading leaderboard...</td></tr>`;

  try {
    const res = await fetch(`/api/leaderboard/${type}`);
    const data = await res.json();

    headerRow.innerHTML = headers[type].map(h => `<th>${h}</th>`).join("");
    tbody.innerHTML = "";

    if (!data.entries?.length) {
      tbody.innerHTML = `<tr><td colspan="${cols}">No results available.</td></tr>`;
      return;
    }

    data.entries.forEach((entry, index) => {
      const row = document.createElement("tr");

      switch (type) {
        case "kingdoms":
          row.innerHTML = `
            <td>${index + 1}</td>
            <td>${escapeHTML(entry.kingdom_name)}</td>
            <td>${escapeHTML(entry.ruler_name)}</td>
            <td>${entry.power_score}</td>
            <td>${entry.economy_score}</td>
          `;
          break;

        case "alliances":
          row.innerHTML = `
            <td>${index + 1}</td>
            <td>${escapeHTML(entry.alliance_name)}</td>
            <td>${entry.military_score}</td>
            <td>${entry.economy_score}</td>
            <td>${entry.diplomacy_score}</td>
            <td>${entry.war_wins}</td>
            <td>${entry.war_losses}</td>
            <td>${entry.prestige_score ?? "—"}</td>
            <td><button class="action-btn apply-btn" data-alliance-id="${entry.alliance_id}" data-alliance-name="${escapeHTML(entry.alliance_name)}">Apply</button></td>
          `;
          break;

        case "wars":
          row.innerHTML = `
            <td>${index + 1}</td>
            <td>${escapeHTML(entry.kingdom_name)}</td>
            <td>${escapeHTML(entry.ruler_name)}</td>
            <td>${entry.battles_won}</td>
            <td>${entry.battles_lost}</td>
          `;
          break;

        case "economy":
          row.innerHTML = `
            <td>${index + 1}</td>
            <td>${escapeHTML(entry.kingdom_name)}</td>
            <td>${escapeHTML(entry.ruler_name)}</td>
            <td>${entry.total_trade_value}</td>
            <td>${entry.market_share}%</td>
          `;
          break;
      }

      tbody.appendChild(row);
    });

    // Bind Apply Buttons if Alliance tab
    if (type === "alliances") {
      document.querySelectorAll(".apply-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const allianceId = btn.dataset.allianceId;
          const allianceName = btn.dataset.allianceName;
          openApplyModal(allianceId, allianceName);
        });
      });
    }

    document.getElementById("last-updated").textContent =
      `Last updated: ${new Date().toLocaleTimeString()}`;

  } catch (err) {
    console.error(`❌ Error loading ${type} leaderboard:`, err);
    tbody.innerHTML = `<tr><td colspan="${cols}">Failed to load leaderboard.</td></tr>`;
  }
}

// ✉️ Alliance application modal
function openApplyModal(allianceId, allianceName) {
  const modal = document.getElementById("apply-modal");
  const modalContent = modal.querySelector(".modal-content");

  modalContent.innerHTML = `
    <h3>Apply to ${escapeHTML(allianceName)}</h3>
    <textarea id="application-message" placeholder="Write your application message..."></textarea>
    <br>
    <button class="action-btn" id="submit-application">Submit Application</button>
    <button class="action-btn" id="close-application">Cancel</button>
  `;

  modal.classList.remove("hidden");

  document.getElementById("submit-application").addEventListener("click", async () => {
    const message = document.getElementById("application-message").value.trim();
    if (!message) return alert("Please enter a message.");

    try {
      const res = await fetch("/api/alliance_members/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alliance_id: allianceId, message })
      });

      const result = await res.json();
      if (!res.ok) throw new Error(result.error || "Application failed.");

      alert(result.message || "Application submitted!");
      modal.classList.add("hidden");
    } catch (err) {
      console.error("❌ Application error:", err);
      alert("Application failed.");
    }
  });

  document.getElementById("close-application").addEventListener("click", () => {
    modal.classList.add("hidden");
  });
}

// 🧼 Basic HTML escape
