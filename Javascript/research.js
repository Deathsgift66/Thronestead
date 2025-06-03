// research.js — FINAL AAA/SSS VERSION — 6.2.25
// Research Nexus Page Controller — FINAL architecture

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  // ✅ Initial load
  await loadResearchNexus();
});

// ✅ Load Research Nexus
async function loadResearchNexus() {
  const treeEl = document.getElementById('tech-tree');
  const detailsEl = document.getElementById('tech-details');
  const activeEl = document.getElementById('active-research');
  const filtersEl = document.getElementById('tech-filters');
  const encyclopediaEl = document.getElementById('encyclopedia');
  const completedEl = document.getElementById('completed-research');
  const toastEl = document.getElementById('toast');

  // Placeholders
  treeEl.innerHTML = "<p>Loading tech tree...</p>";
  detailsEl.innerHTML = "<p>Select a technology to view details.</p>";
  activeEl.innerHTML = "<p>Loading active research...</p>";
  filtersEl.innerHTML = "<p>Loading filters...</p>";
  encyclopediaEl.innerHTML = "<p>Loading encyclopedia...</p>";
  completedEl.innerHTML = "<p>Loading completed research...</p>";

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

    // ✅ Load tech catalogue
    const { data: catalogueData, error: catalogueError } = await supabase
      .from('tech_catalogue')
      .select('*');

    if (catalogueError) throw catalogueError;

    // ✅ Load kingdom research tracking
    const { data: trackingData, error: trackingError } = await supabase
      .from('kingdom_research_tracking')
      .select('*')
      .eq('kingdom_id', kingdomId);

    if (trackingError) throw trackingError;

    // ✅ Separate completed and active research
    const activeResearch = trackingData.find(t => t.status === "active");
    const completedResearch = trackingData.filter(t => t.status === "completed");

    // ✅ Render filters
    renderTechFilters(catalogueData);

    // ✅ Render tech tree
    renderTechTree(catalogueData, trackingData);

    // ✅ Render active research
    renderActiveResearch(activeResearch, catalogueData);

    // ✅ Render completed research
    renderCompletedResearch(completedResearch, catalogueData);

    // ✅ Render encyclopedia
    renderEncyclopedia(completedResearch, catalogueData);

    // ✅ Start timers
    startCountdownTimers();

  } catch (err) {
    console.error("❌ Error loading Research Nexus:", err);
    showToast("Failed to load Research Nexus.");
  }
}

// ✅ Render Tech Filters
function renderTechFilters(catalogue) {
  const filtersEl = document.getElementById('tech-filters');
  filtersEl.innerHTML = "";

  const categories = [...new Set(catalogue.map(t => t.category))].sort();

  categories.forEach(category => {
    const btn = document.createElement("button");
    btn.classList.add("action-btn");
    btn.textContent = category;
    btn.addEventListener("click", () => filterTechTree(category));
    filtersEl.appendChild(btn);
  });

  // Add "Show All"
  const showAllBtn = document.createElement("button");
  showAllBtn.classList.add("action-btn");
  showAllBtn.textContent = "Show All";
  showAllBtn.addEventListener("click", () => filterTechTree("ALL"));
  filtersEl.appendChild(showAllBtn);
}

// ✅ Render Tech Tree
function renderTechTree(catalogue, tracking) {
  const treeEl = document.getElementById('tech-tree');
  treeEl.innerHTML = "";

  catalogue.forEach(tech => {
    const isCompleted = tracking.some(t => t.tech_code === tech.tech_code && t.status === "completed");
    const isActive = tracking.some(t => t.tech_code === tech.tech_code && t.status === "active");

    const node = document.createElement("div");
    node.classList.add("tech-node");

    if (isCompleted) node.classList.add("completed");
    if (isActive) node.classList.add("active");

    node.innerHTML = `
      <h4>${escapeHTML(tech.name)}</h4>
      <p>Tier: ${tech.tier}</p>
      <p>Category: ${escapeHTML(tech.category)}</p>
    `;

    node.addEventListener("click", () => showTechDetails(tech, isCompleted, isActive));
    treeEl.appendChild(node);
  });
}

// ✅ Show Tech Details
function showTechDetails(tech, isCompleted, isActive) {
  const detailsEl = document.getElementById('tech-details');

  detailsEl.innerHTML = `
    <h3>${escapeHTML(tech.name)}</h3>
    <p>${escapeHTML(tech.description)}</p>
    <p>Tier: ${tech.tier}</p>
    <p>Category: ${escapeHTML(tech.category)}</p>
    <p>Status: ${isCompleted ? "Completed" : isActive ? "In Progress" : "Not Started"}</p>
    <p>Duration: ${tech.duration_hours}h</p>
    ${!isCompleted && !isActive ? `<button class="action-btn" id="start-research-btn">Start Research</button>` : ""}
  `;

  if (!isCompleted && !isActive) {
    document.getElementById('start-research-btn').addEventListener("click", async () => {
      if (!confirm(`Start research on "${tech.name}"?`)) return;

      try {
        const res = await fetch("/api/kingdom/start_research", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tech_code: tech.tech_code })
        });

        const result = await res.json();

        if (!res.ok) throw new Error(result.error || "Failed to start research.");

        showToast("Research started!");
        await loadResearchNexus();

      } catch (err) {
        console.error("❌ Error starting research:", err);
        showToast("Failed to start research.");
      }
    });
  }
}

// ✅ Filter Tech Tree
function filterTechTree(category) {
  const allNodes = document.querySelectorAll('.tech-node');

  allNodes.forEach(node => {
    if (category === "ALL") {
      node.style.display = "block";
    } else {
      const nodeCategory = node.querySelector("p:nth-child(3)").textContent.replace("Category: ", "");
      node.style.display = nodeCategory === category ? "block" : "none";
    }
  });
}

// ✅ Render Active Research
function renderActiveResearch(activeResearch, catalogue) {
  const activeEl = document.getElementById('active-research');
  activeEl.innerHTML = "";

  if (!activeResearch) {
    activeEl.innerHTML = "<p>No active research.</p>";
    return;
  }

  const techDef = catalogue.find(t => t.tech_code === activeResearch.tech_code);
  const remainingTime = Math.max(0, Math.floor((new Date(activeResearch.ends_at).getTime() - Date.now()) / 1000));

  const card = document.createElement("div");
  card.classList.add("tech-card");

  card.innerHTML = `
    <h3>${escapeHTML(techDef?.name || activeResearch.tech_code)}</h3>
    <p>${escapeHTML(techDef?.description || "")}</p>
    <p>Time Remaining: <span class="countdown" data-ends-at="${activeResearch.ends_at}">${formatTime(remainingTime)}</span></p>
  `;

  activeEl.appendChild(card);
}

// ✅ Render Completed Research
function renderCompletedResearch(completedResearch, catalogue) {
  const completedEl = document.getElementById('completed-research');
  completedEl.innerHTML = "";

  if (completedResearch.length === 0) {
    completedEl.innerHTML = "<p>No completed research.</p>";
    return;
  }

  completedResearch.forEach(r => {
    const techDef = catalogue.find(t => t.tech_code === r.tech_code);

    const card = document.createElement("div");
    card.classList.add("tech-card");

    card.innerHTML = `
      <h3>${escapeHTML(techDef?.name || r.tech_code)}</h3>
      <p>${escapeHTML(techDef?.description || "")}</p>
      <p>Completed on: ${new Date(r.ends_at).toLocaleString()}</p>
    `;

    completedEl.appendChild(card);
  });
}

// ✅ Render Encyclopedia
function renderEncyclopedia(completedResearch, catalogue) {
  const encyclopediaEl = document.getElementById('encyclopedia');
  encyclopediaEl.innerHTML = "";

  if (completedResearch.length === 0) {
    encyclopediaEl.innerHTML = "<p>No unlocked technologies yet.</p>";
    return;
  }

  completedResearch.forEach(r => {
    const techDef = catalogue.find(t => t.tech_code === r.tech_code);

    const entry = document.createElement("div");
    entry.classList.add("tech-card");

    entry.innerHTML = `
      <h3>${escapeHTML(techDef?.name || r.tech_code)}</h3>
      <p>${escapeHTML(techDef?.encyclopedia_entry || "No lore available.")}</p>
    `;

    encyclopediaEl.appendChild(entry);
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
  const toastEl = document.getElementById('toast');
  toastEl.textContent = msg;
  toastEl.classList.add("show");

  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
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
