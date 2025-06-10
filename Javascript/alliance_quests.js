/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_quests.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let currentFilter = 'active';
let questChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Initial load
  await loadQuests("active");

  questChannel = supabase
    .channel('public:quest_alliance_tracking')
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'quest_alliance_tracking' },
      () => {
        loadQuests(currentFilter);
      }
    )
    .subscribe();

  // ✅ Filter tabs
  document.querySelectorAll(".filter-tab").forEach(tab => {
    tab.addEventListener("click", async () => {
      document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const filter = tab.dataset.filter;
      await loadQuests(filter);
    });
  });

  // ✅ Start new quest button
  const startBtn = document.getElementById("start-new-quest");
  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      const questId = prompt("Enter Quest ID to start:");
      if (!questId) return;
      const res = await fetch("/api/alliance-quests/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quest_code: questId })
      });
      const data = await res.json();
      alert(data.message || "Quest started.");
      await loadQuests("active");
    });
  }

  // ✅ Modal close button
  const closeBtn = document.querySelector(".close-button");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      document.getElementById("quest-modal").classList.remove("open");
    });
  }

  // ✅ Accept quest button
  const acceptBtn = document.getElementById("accept-quest-button");
  if (acceptBtn) {
    acceptBtn.addEventListener("click", async () => {
      const questId = acceptBtn.dataset.questId;
      if (!questId) return;
      const res = await fetch("/api/alliance-quests/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quest_code: questId })
      });
      const result = await res.json();
      alert(result.message || "Quest accepted!");
      document.getElementById("quest-modal").classList.remove("open");
      await loadQuests("active");
    });
  }

  window.addEventListener('beforeunload', () => {
    if (questChannel) supabase.removeChannel(questChannel);
  });
});

// ✅ Load quests by status
async function loadQuests(status) {
  currentFilter = status;
  const board = document.getElementById("quest-board");
  const heroes = document.getElementById("hero-list");

  board.innerHTML = "<p>Loading quests...</p>";
  heroes.innerHTML = "<li>Loading heroes...</li>";

  try {
    let endpoint;
    if (status === "active") {
      endpoint = "/api/alliance-quests/active";
    } else if (status === "completed") {
      endpoint = "/api/alliance-quests/completed";
    } else {
      endpoint = "/api/alliance-quests/available";
    }
    const res = await fetch(endpoint);
    const data = await res.json();
    const quests = data.quests || data;

    // Clear board
    board.innerHTML = "";
    heroes.innerHTML = "";

    if (!quests || quests.length === 0) {
      document.getElementById("no-quests-message").classList.remove("hidden");
      return;
    } else {
      document.getElementById("no-quests-message").classList.add("hidden");
    }

    // Render quests
    quests.forEach(q => {
      const card = document.createElement("div");
      card.classList.add("quest-card");

      card.innerHTML = `
        <div class="quest-header">
          <span class="quest-title" title="${q.goal_desc}">${q.title}</span>
          <span class="quest-type">[${q.type}]</span>
        </div>
        <p class="quest-lore">${q.lore}</p>
        <p class="quest-details">${q.goal_desc}</p>
        <div class="quest-progress">
          <div class="quest-progress-bar">
            <div class="quest-progress-bar-inner" style="width: ${q.progress}%"></div>
          </div>
          <span class="progress-label">${q.progress}%</span>
        </div>
        <div class="quest-rewards">🎁 Rewards: ${q.reward_gold} gold${q.reward_item ? ", " + q.reward_item : ""}</div>
        ${q.leader_note ? `<div class="quest-leader-note">🖋 Leader Note: ${q.leader_note}</div>` : ""}
        <div class="quest-actions">
          <button class="view-quest-btn" data-code="${q.quest_code}">📜 View Details</button>
        </div>
      `;

      board.appendChild(card);
    });

    // Add event listeners for View Details
    document.querySelectorAll(".view-quest-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const code = btn.dataset.code;
        const resDetail = await fetch(`/api/alliance-quests/detail/${code}`);
        const quest = await resDetail.json();
        openQuestModal(quest);
      });
    });

    // Render Hall of Heroes
    const heroData = data.heroes || [];
    if (heroData.length > 0) {
      heroData.forEach(h => {
        const li = document.createElement("li");
        li.textContent = `${h.name} — ${h.contributions} pts`;
        heroes.appendChild(li);
      });
    } else {
      heroes.innerHTML = "<li>No heroes yet.</li>";
    }

  } catch (err) {
    console.error("❌ Error loading quests:", err);
    board.innerHTML = "<p>Failed to load quests.</p>";
    heroes.innerHTML = "<li>Failed to load heroes.</li>";
  }
}

// ✅ Open Quest Modal
function openQuestModal(q) {
  const modal = document.getElementById("quest-modal");

  document.getElementById("modal-quest-title").textContent = q.name || q.title;
  document.querySelector(".quest-type-modal").textContent = q.category ? `[${q.category}]` : q.type ? `[${q.type}]` : '';
  document.getElementById("modal-quest-description").textContent = q.description || q.lore || '';

  // Contributions
  const contribList = document.getElementById("modal-quest-contributions");
  contribList.innerHTML = "";
  if (q.contributions && q.contributions.length > 0) {
    q.contributions.forEach(c => {
      const li = document.createElement("li");
      li.textContent = `${c.player_name}: ${c.amount} ${c.resource_type}`;
      contribList.appendChild(li);
    });
  } else {
    contribList.innerHTML = "<li>No specific contributions listed.</li>";
  }

  // Rewards
  const rewardsList = document.getElementById("modal-quest-rewards");
  rewardsList.innerHTML = "";
  if (q.rewards) {
    Object.entries(q.rewards).forEach(([k, v]) => {
      const li = document.createElement("li");
      li.textContent = `${k}: ${v}`;
      rewardsList.appendChild(li);
    });
  }

  // Time Left
  document.getElementById("modal-time-left").textContent = q.ends_at || "Unknown";

  // Leader Note
  const leaderNote = document.getElementById("modal-quest-leader-note");
  if (q.leader_note) {
    leaderNote.textContent = `🖋 ${q.leader_note}`;
    leaderNote.classList.remove("hidden");
  } else {
    leaderNote.textContent = "";
    leaderNote.classList.add("hidden");
  }

  // Accept button
  const acceptBtn = document.getElementById("accept-quest-button");
  if (acceptBtn) {
    if (q.status !== 'completed') {
      acceptBtn.classList.remove("hidden");
      acceptBtn.dataset.questId = q.quest_code;
      document.getElementById("role-check-message").textContent = "";
    } else {
      acceptBtn.classList.add("hidden");
      document.getElementById("role-check-message").textContent = "Quest already completed.";
    }
  }

  // Open modal
  modal.classList.add("open");
}

