// quest_alliance.js — FINAL AAA/SSS VERSION — 6.2.25
// Alliance Quest Center — FINAL architecture

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

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
    // ✅ Fetch user + alliance ID
    const { data: { user } } = await supabase.auth.getUser();

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('alliance_id, alliance_role')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const allianceId = userData.alliance_id;
    const allianceRole = userData.alliance_role;

    // ✅ Fetch catalogue
    const { data: catalogueData, error: catalogueError } = await supabase
      .from('quest_alliance_catalogue')
      .select('*');

    if (catalogueError) throw catalogueError;

    // ✅ Fetch alliance quests
    const { data: allianceQuestsData, error: allianceQuestsError } = await supabase
      .from('quest_alliance_tracking')
      .select('*')
      .eq('alliance_id', allianceId);

    if (allianceQuestsError) throw allianceQuestsError;

    // ✅ Fetch contribution log
    const { data: contributionData, error: contributionError } = await supabase
      .from('quest_alliance_contributions')
      .select('*')
      .eq('alliance_id', allianceId)
      .order('timestamp', { ascending: false })
      .limit(25);

    if (contributionError) throw contributionError;

    // ✅ Separate active/completed quests
    const activeQuests = allianceQuestsData.filter(q => q.status === "active");
    const completedQuests = allianceQuestsData.filter(q => q.status === "completed");

    // ✅ Render quest catalogue
    renderQuestCatalogue(catalogueData, allianceQuestsData, allianceRole);

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

    card.innerHTML = `
      <h3>${escapeHTML(quest.name)}</h3>
      <p>${escapeHTML(quest.description)}</p>
      <p>Duration: ${quest.duration_hours}h</p>
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
        const res = await fetch("/api/alliance/accept_quest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
