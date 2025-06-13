/*
Project Name: Kingmakers Rise Frontend
File Name: quests.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let questChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  // ✅ Initial load
  await loadKingdomQuests();

  questChannel = supabase
    .channel('public:quest_kingdom_tracking')
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'quest_kingdom_tracking' },
      async () => {
        await loadKingdomQuests();
      }
    )
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (questChannel) supabase.removeChannel(questChannel);
  });
});

// ✅ Load Kingdom Quests
async function loadKingdomQuests() {
  const catalogueEl = document.getElementById('quest-catalogue');
  const activeEl = document.getElementById('active-quests');
  const completedEl = document.getElementById('completed-quests');

  // Placeholders while loading
  catalogueEl.innerHTML = "<p>Loading quest catalogue...</p>";
  activeEl.innerHTML = "<p>Loading active quests...</p>";
  completedEl.innerHTML = "<p>Loading completed quests...</p>";

  try {
    // ✅ Load user
    const { data: { user } } = await supabase.auth.getUser();

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const kingdomId = userData.kingdom_id;

    // ✅ Load quest catalogue
    const castleLevel = window.playerProgression?.castleLevel || 1;

    const { data: catalogueData, error: catalogueError } = await supabase
      .from('quest_kingdom_catalogue')
      .select('*')
      .eq('is_active', true)
      .lte('required_level', castleLevel);

    if (catalogueError) throw catalogueError;

    // ✅ Load kingdom quest tracking
    const { data: trackingData, error: trackingError } = await supabase
      .from('quest_kingdom_tracking')
      .select('*')
      .eq('kingdom_id', kingdomId);

    if (trackingError) throw trackingError;

    // ✅ Separate active/completed quests
    const activeQuests = trackingData.filter(q => q.status === "active");
    const completedQuests = trackingData.filter(q => q.status === "completed");

    // ✅ Render sections
    renderQuestCatalogue(catalogueData, trackingData);
    renderActiveQuests(activeQuests, catalogueData);
    renderCompletedQuests(completedQuests, catalogueData);

    // ✅ Start timers
    startCountdownTimers();

  } catch (err) {
    console.error("❌ Error loading kingdom quests:", err);
    catalogueEl.innerHTML = "<p>Failed to load quest catalogue.</p>";
    activeEl.innerHTML = "<p>Failed to load active quests.</p>";
    completedEl.innerHTML = "<p>Failed to load completed quests.</p>";
  }
}

// ✅ Render Quest Catalogue
function renderQuestCatalogue(catalogue, tracking) {
  const container = document.getElementById('quest-catalogue');
  container.innerHTML = "";

  const activeQuestCodes = tracking
    .filter(q => q.status === "active")
    .map(q => q.quest_code);
  const completedQuestCodes = tracking
    .filter(q => q.status === "completed")
    .map(q => q.quest_code);

  catalogue.forEach(quest => {
    const isActive = activeQuestCodes.includes(quest.quest_code);
    const isCompleted = completedQuestCodes.includes(quest.quest_code);

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
      <button class="action-btn accept-quest-btn" data-code="${quest.quest_code}" ${isActive || (!quest.repeatable && isCompleted) ? "disabled" : ""}>
        ${isActive ? "Already Active" : (!quest.repeatable && isCompleted) ? "Completed" : "Accept Quest"}
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
        const res = await fetch("/api/kingdom/accept_quest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ quest_code: questCode })
        });

        const result = await res.json();

        if (!res.ok) throw new Error(result.error || "Failed to accept quest.");

        showToast("Quest accepted!");
        await loadKingdomQuests();

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
