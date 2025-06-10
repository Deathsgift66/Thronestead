/*
Project Name: Kingmakers Rise Frontend
File Name: quest_alliance.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

async function fetchWithAuth(url, options = {}) {
  const { data: { user } } = await supabase.auth.getUser();
  const headers = options.headers || {};
  headers['X-User-ID'] = user.id;
  return fetch(url, { ...options, headers });
}

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  // ✅ Initial load
  await loadAllianceQuests();
});

// ✅ Load Alliance Quests
async function loadAllianceQuests() {
  const questCatalogueEl = document.getElementById('quest-catalogue');
  const activeQuestsEl = document.getElementById('active-quests');
  const completedQuestsEl = document.getElementById('completed-quests');
  const contributionLogEl = document.getElementById('contribution-log');

  // Placeholders while loading
  questCatalogueEl.innerHTML = "<p>Loading quest catalogue...</p>";
  activeQuestsEl.innerHTML = "<p>Loading active quests...</p>";
  completedQuestsEl.innerHTML = "<p>Loading completed quests...</p>";
  contributionLogEl.innerHTML = "<p>Loading contribution log...</p>";

  try {
    const [catalogueRes, activeRes, completedRes, contribRes] = await Promise.all([
      fetchWithAuth('/api/alliance-quests/catalogue'),
      fetchWithAuth('/api/alliance-quests/active'),
      fetchWithAuth('/api/alliance-quests/completed'),
      fetchWithAuth('/api/alliance-quests/contributions'),
    ]);

    const catalogueData = await catalogueRes.json();
    const activeData = await activeRes.json();
    const completedData = await completedRes.json();
    const contributionData = await contribRes.json();

    const allianceRole = window.user?.alliance_role || 'Member';

    const activeQuests = activeData;
    const completedQuests = completedData;

    // ✅ Render quest catalogue
    renderQuestCatalogue(catalogueData, [...activeQuests, ...completedQuests], allianceRole);

    // ✅ Render active quests
    renderActiveQuests(activeQuests, catalogueData);

    // ✅ Render completed quests
    renderCompletedQuests(completedQuests, catalogueData);

    // ✅ Render contribution log
    renderContributionLog(contributionData);

    // ✅ Start countdowns
    startCountdownTimers();

  } catch (err) {
    console.error("❌ Error loading alliance quests:", err);
    questCatalogueEl.innerHTML = "<p>Failed to load quest catalogue.</p>";
    activeQuestsEl.innerHTML = "<p>Failed to load active quests.</p>";
    completedQuestsEl.innerHTML = "<p>Failed to load completed quests.</p>";
    contributionLogEl.innerHTML = "<p>Failed to load contribution log.</p>";
  }
}

// ✅ Render Quest Catalogue
function renderQuestCatalogue(catalogue, allianceQuests, role) {
  const container = document.getElementById('quest-catalogue');
  container.innerHTML = "";

  const activeQuestCodes = allianceQuests
    .filter(q => q.status === "active")
    .map(q => q.quest_code);

  catalogue.forEach(quest => {
    const isActive = activeQuestCodes.includes(quest.quest_code);

    const card = document.createElement("div");
    card.classList.add("quest-card");

    const objectives = formatJsonList(quest.objectives);
    const rewards = formatJsonList(quest.rewards);

    card.innerHTML = `
      <h3>${escapeHTML(quest.name)}</h3>
      <p>${escapeHTML(quest.description)}</p>
      <p>Category: ${escapeHTML(quest.category || '')}</p>
      <p><strong>Objectives:</strong></p>
      <ul>${objectives}</ul>
      <p><strong>Rewards:</strong></p>
      <ul>${rewards}</ul>
      <p>Duration: ${quest.duration_hours}h</p>
      <p>${quest.repeatable ? `Repeatable${quest.max_attempts ? ` (Max ${quest.max_attempts})` : ''}` : 'One-time'}</p>
      <button class="action-btn accept-quest-btn" data-code="${quest.quest_code}" ${isActive || !canStartQuest(role) ? "disabled" : ""}>
        ${isActive ? "Already Active" : canStartQuest(role) ? "Accept Quest" : "Insufficient Rank"}
      </button>
    `;

    container.appendChild(card);
  });

  // ✅ Bind accept buttons
  document.querySelectorAll(".accept-quest-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const questCode = btn.dataset.code;
      if (!confirm(`Accept quest "${questCode}"?`)) return;

      try {
        const res = await fetchWithAuth('/api/alliance-quests/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ quest_code: questCode })
        });

        const result = await res.json();

        if (!res.ok) throw new Error(result.error || "Failed to accept quest.");

        showToast("Quest accepted!");
        await loadAllianceQuests();

      } catch (err) {
        console.error("❌ Error accepting quest:", err);
        showToast("Failed to accept quest.");
      }
    });
  });
}

// ✅ Render Active Quests
function renderActiveQuests(activeQuests, catalogue) {
  const container = document.getElementById('active-quests');
  container.innerHTML = "";

  if (activeQuests.length === 0) {
    container.innerHTML = "<p>No active quests.</p>";
    return;
  }

  activeQuests.forEach(q => {
    const questDef = catalogue.find(def => def.quest_code === q.quest_code);
    const remainingTime = Math.max(0, Math.floor((new Date(q.ends_at).getTime() - Date.now()) / 1000));

    const card = document.createElement("div");
    card.classList.add("quest-card");

    card.innerHTML = `
      <h3>${escapeHTML(questDef?.name || q.quest_code)}</h3>
      <p>${escapeHTML(questDef?.description || "")}</p>
      <p>Time Remaining: <span class="countdown" data-ends-at="${q.ends_at}">${formatTime(remainingTime)}</span></p>
      <p>Progress: ${q.progress}%</p>
    `;

    container.appendChild(card);
  });
}

// ✅ Render Completed Quests
function renderCompletedQuests(completedQuests, catalogue) {
  const container = document.getElementById('completed-quests');
  container.innerHTML = "";

  if (completedQuests.length === 0) {
    container.innerHTML = "<p>No completed quests.</p>";
    return;
  }

  completedQuests.forEach(q => {
    const questDef = catalogue.find(def => def.quest_code === q.quest_code);

    const card = document.createElement("div");
    card.classList.add("quest-card");

    card.innerHTML = `
      <h3>${escapeHTML(questDef?.name || q.quest_code)}</h3>
      <p>${escapeHTML(questDef?.description || "")}</p>
      <p>Completed on: ${new Date(q.ends_at).toLocaleString()}</p>
    `;

    container.appendChild(card);
  });
}

// ✅ Render Contribution Log
function renderContributionLog(contributions) {
  const container = document.getElementById('contribution-log');
  container.innerHTML = "";

  if (contributions.length === 0) {
    container.innerHTML = "<p>No contributions yet.</p>";
    return;
  }

  const list = document.createElement("ul");
  contributions.forEach(entry => {
    const li = document.createElement("li");
    li.innerHTML = `
      [${new Date(entry.timestamp).toLocaleString()}] 
      ${escapeHTML(entry.player_name)} contributed ${entry.amount} ${escapeHTML(entry.resource_type)}
    `;
    list.appendChild(li);
  });

  container.appendChild(list);
}

// ✅ Start Countdown Timers
function startCountdownTimers() {
  const countdownEls = document.querySelectorAll(".countdown");

  countdownEls.forEach(el => {
    const endsAt = new Date(el.dataset.endsAt).getTime();

    const update = () => {
      const remaining = Math.max(0, Math.floor((endsAt - Date.now()) / 1000));
      el.textContent = formatTime(remaining);

      if (remaining > 0) {
        requestAnimationFrame(update);
      } else {
        el.textContent = "Completed!";
      }
    };

    update();
  });
}

// ✅ Helper: Role Check
function canStartQuest(role) {
  const roleHierarchy = ["Member", "Officer", "Elder", "Co-Leader", "Leader"];
  return roleHierarchy.indexOf(role) >= roleHierarchy.indexOf("Officer");
}

// ✅ Helper: Format Time
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  return `${h}h ${m}m ${s}s`;
}

// ✅ Helper: Toast
function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = msg;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
      document.body.removeChild(toast);
    }, 3000);
  }, 100);
}

// ✅ Helper: Format JSON object to list items
function formatJsonList(data) {
  if (!data) return '<li>None</li>';
  try {
    const obj = typeof data === 'string' ? JSON.parse(data) : data;
    const items = [];
    for (const [key, val] of Object.entries(obj)) {
      if (typeof val === 'object') {
        const inner = Object.entries(val)
          .map(([k, v]) => `${escapeHTML(k)}: ${escapeHTML(String(v))}`)
          .join(', ');
        items.push(`<li>${escapeHTML(key)} — ${inner}</li>`);
      } else {
        items.push(`<li>${escapeHTML(key)}: ${escapeHTML(String(val))}</li>`);
      }
    }
    return items.join('');
  } catch (err) {
    return `<li>${escapeHTML(String(data))}</li>`;
  }
}

// ✅ Helper: Escape HTML
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
