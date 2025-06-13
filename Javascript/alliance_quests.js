// Project Name: Kingmakers Rise©
// File Name: alliance_quests.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

let currentFilter = 'active';
let questChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Logout
  document.getElementById("logout-btn")?.addEventListener("click", async () => {
    await supabase.auth.signOut();
    window.location.href = "index.html";
  });

  // ✅ Initial Load
  await loadQuests("active");

  // ✅ Realtime Sync
  questChannel = supabase
    .channel('public:quest_alliance_tracking')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'quest_alliance_tracking'
    }, () => loadQuests(currentFilter))
    .subscribe();

  // ✅ Filter Tabs
  document.querySelectorAll(".filter-tab").forEach(tab => {
    tab.addEventListener("click", async () => {
      document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      await loadQuests(tab.dataset.filter);
    });
  });

  // ✅ Start Quest (Admin only)
  document.getElementById("start-new-quest")?.addEventListener("click", async () => {
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

  // ✅ Modal controls
  document.querySelector(".close-button")?.addEventListener("click", () => {
    document.getElementById("quest-modal").classList.remove("open");
  });

  document.getElementById("accept-quest-button")?.addEventListener("click", async e => {
    const questId = e.target.dataset.questId;
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

  document.getElementById("claim-reward-button")?.addEventListener("click", async e => {
    const questId = e.target.dataset.questId;
    if (!questId) return;
    const res = await fetch("/api/alliance-quests/claim", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quest_code: questId })
    });
    const result = await res.json();
    alert(result.message || "Reward claimed!");
    document.getElementById("quest-modal").classList.remove("open");
    await loadQuests("completed");
  });

  window.addEventListener('beforeunload', () => {
    if (questChannel) supabase.removeChannel(questChannel);
  });
});

// ✅ Load quests by filter
async function loadQuests(status) {
  currentFilter = status;
  const board = document.getElementById("quest-board");
  const heroes = document.getElementById("hero-list");
  const noMsg = document.getElementById("no-quests-message");

  board.innerHTML = "<p>Loading quests...</p>";
  heroes.innerHTML = "<li>Loading heroes...</li>";

  try {
    const endpoint = {
      active: "/api/alliance-quests/active",
      completed: "/api/alliance-quests/completed"
    }[status] || "/api/alliance-quests/available";

    const res = await fetch(endpoint);
    const data = await res.json();
    const quests = data.quests || data;

    board.innerHTML = "";
    heroes.innerHTML = "";

    if (!quests.length) {
      noMsg?.classList.remove("hidden");
      return;
    }
    noMsg?.classList.add("hidden");

    quests.forEach(q => board.appendChild(renderQuestCard(q)));

    document.querySelectorAll(".view-quest-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const code = btn.dataset.code;
        const resDetail = await fetch(`/api/alliance-quests/detail/${code}`);
        const quest = await resDetail.json();
        openQuestModal(quest);
      });
    });

    const heroData = data.heroes || [];
    heroes.innerHTML = heroData.length
      ? heroData.map(h => `<li>${escapeHTML(h.name)} — ${h.contributions} pts</li>`).join('')
      : "<li>No heroes yet.</li>";

  } catch (err) {
    console.error("❌ Error loading quests:", err);
    board.innerHTML = "<p>Failed to load quests.</p>";
    heroes.innerHTML = "<li>Failed to load heroes.</li>";
  }
}

// ✅ Quest Card Renderer
function renderQuestCard(q) {
  const div = document.createElement("div");
  div.className = "quest-card";
  div.innerHTML = `
    <div class="quest-header">
      <span class="quest-title" title="${escapeHTML(q.goal_desc)}">${escapeHTML(q.title)}</span>
      <span class="quest-type">[${escapeHTML(q.type)}]</span>
    </div>
    <p class="quest-lore">${escapeHTML(q.lore)}</p>
    <p class="quest-details">${escapeHTML(q.goal_desc)}</p>
    <div class="quest-progress">
      <div class="quest-progress-bar">
        <div class="quest-progress-bar-inner" style="width:${q.progress}%"></div>
      </div>
      <span class="progress-label">${q.progress}%</span>
    </div>
    <div class="quest-rewards">🎁 Rewards: ${q.reward_gold} gold${q.reward_item ? ', ' + escapeHTML(q.reward_item) : ''}</div>
    ${q.leader_note ? `<div class="quest-leader-note">🖋 Leader Note: ${escapeHTML(q.leader_note)}</div>` : ""}
    <div class="quest-actions">
      <button class="view-quest-btn" data-code="${q.quest_code}">📜 View Details</button>
    </div>
  `;
  return div;
}

// ✅ Modal Viewer
function openQuestModal(q) {
  const modal = document.getElementById("quest-modal");

  document.getElementById("modal-quest-title").textContent = q.name ? escapeHTML(q.name) : escapeHTML(q.title);
  document.querySelector(".quest-type-modal").textContent = q.category
    ? `[${escapeHTML(q.category)}]`
    : q.type ? `[${escapeHTML(q.type)}]` : '';

  document.getElementById("modal-quest-description").textContent = q.description
    ? escapeHTML(q.description) : q.lore ? escapeHTML(q.lore) : '';

  const contribList = document.getElementById("modal-quest-contributions");
  contribList.innerHTML = "";
  (q.contributions?.length ? q.contributions : []).forEach(c => {
    const li = document.createElement("li");
    li.textContent = `${c.player_name}: ${c.amount} ${c.resource_type}`;
    contribList.appendChild(li);
  });
  if (!q.contributions?.length) contribList.innerHTML = "<li>No specific contributions listed.</li>";

  const rewardsList = document.getElementById("modal-quest-rewards");
  rewardsList.innerHTML = "";
  if (q.rewards) {
    Object.entries(q.rewards).forEach(([type, reward]) => {
      const li = document.createElement("li");
      li.textContent = typeof reward === "object"
        ? `${type}: ${Object.entries(reward).map(([k, v]) => `${k} ${v}`).join(", ")}`
        : `${type}: ${reward}`;
      rewardsList.appendChild(li);
    });
  }

  document.getElementById("modal-time-left").textContent = q.ends_at || "Unknown";

  const leaderNote = document.getElementById("modal-quest-leader-note");
  if (q.leader_note) {
    leaderNote.textContent = `🖋 ${q.leader_note}`;
    leaderNote.classList.remove("hidden");
  } else {
    leaderNote.textContent = "";
    leaderNote.classList.add("hidden");
  }

  const acceptBtn = document.getElementById("accept-quest-button");
  if (acceptBtn) {
    acceptBtn.classList.toggle("hidden", q.status === 'completed');
    acceptBtn.dataset.questId = q.quest_code || '';
    document.getElementById("role-check-message").textContent = q.status === 'completed' ? "Quest already completed." : '';
  }

  const claimBtn = document.getElementById("claim-reward-button");
  if (claimBtn) {
    claimBtn.classList.toggle("hidden", !(q.status === 'completed' && !q.reward_claimed));
    claimBtn.dataset.questId = q.quest_code || '';
  }

  modal.classList.add("open");
}

// ✅ Safe string escape
function escapeHTML(str) {
  return String(str || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
