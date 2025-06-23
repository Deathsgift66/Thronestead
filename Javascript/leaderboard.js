// Project Name: Thronestead©
// File Name: leaderboard.js
// Version 6.16.2025.21.20
// Developer: Codex
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';
import { setupTabs } from './components/tabControl.js';
import { authHeaders } from './auth.js';

let currentTab = "kingdoms";

const headers = {
  kingdoms: ["Rank", "Kingdom", "Ruler", "Power", "Economy"],
  alliances: ["Rank", "Alliance", "Military", "Economy", "Diplomacy", "Wins", "Losses", "Prestige", "Apply"],
  wars: ["Rank", "Kingdom", "Ruler", "Wins", "Losses"],
  economy: ["Rank", "Kingdom", "Ruler", "Trade", "Market %"]
};

// 🔐 User session + leaderboard loader
document.addEventListener("DOMContentLoaded", async () => {


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

  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelector('.tab-button.active')?.classList.remove('active');
      document.querySelector('.tab-button[aria-selected="true"]')?.setAttribute('aria-selected', 'false');
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      currentTab = btn.dataset.tab;
      loadLeaderboard(currentTab);
    });
  });
});

// 🧭 Tab switch logic for leaderboard page

// 📊 Load leaderboard by tab type
async function loadLeaderboard(type) {
  const tbody = document.getElementById('leaderboard-body');
  const headerRow = document.getElementById('leaderboard-headers');
  const cols = headers[type]?.length || 5;

  tbody.innerHTML = `<tr><td colspan="${cols}">Loading ${type} leaderboard...</td></tr>`;

  try {
    const res = await fetch(`/api/leaderboard/${type}?limit=100`, {
      headers: await authHeaders()
    });
    const data = await res.json();

    headerRow.innerHTML = headers[type].map(h => `<th scope="col">${h}</th>`).join("");
    tbody.innerHTML = "";

    if (!data.entries?.length) {
      tbody.innerHTML = `<tr><td colspan="${cols}">No results available.</td></tr>`;
      return;
    }

    data.entries.forEach((entry, index) => {
      const row = document.createElement("tr");
      if (entry.is_self) row.classList.add('highlight-current-user');

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
      if (entry.kingdom_id) {
        row.addEventListener('click', () => {
          window.location.href = `kingdom_profile.html?kingdom_id=${entry.kingdom_id}`;
        });
      } else {
        row.addEventListener('click', () => openPreviewModal(entry));
      }

      tbody.appendChild(row);
    });

    // Bind Apply Buttons if Alliance tab
    if (type === 'alliances') {
      document.querySelectorAll('.apply-btn').forEach(btn => {
        btn.addEventListener('click', e => {
          e.stopPropagation();
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
    <button class="action-btn" id="submit-application">Submit Application</button>
    <button class="action-btn" id="close-application">Cancel</button>
  `;

  modal.classList.remove("hidden");

  document.getElementById("submit-application").addEventListener("click", async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      const res = await fetch("/api/alliance_members/apply", {
        method: "POST",
        headers: { ...(await authHeaders()), "Content-Type": "application/json" },
        body: JSON.stringify({
          alliance_id: allianceId,
          user_id: user.id,
          username: user.user_metadata?.username || user.email
        })
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

function openPreviewModal(entry) {
  const modal = document.getElementById('preview-modal');
  if (!modal) return;
  const content = modal.querySelector('.modal-content');
  content.textContent = entry.detail || 'No additional details';
  modal.classList.remove('hidden');
  modal.addEventListener('click', e => {
    if (e.target === modal) modal.classList.add('hidden');
  }, { once: true });
}

// 🧼 Basic HTML escape
