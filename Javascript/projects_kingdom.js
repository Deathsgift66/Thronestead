// Comment
// Project Name: Thronestead©
// File Name: projects_kingdom.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';

const RESOURCE_KEYS = [
  'wood',
  'stone',
  'iron_ore',
  'gold',
  'gems',
  'food',
  'coal',
  'livestock',
  'clay',
  'flax',
  'tools',
  'wood_planks',
  'refined_stone',
  'iron_ingots',
  'charcoal',
  'leather',
  'arrows',
  'swords',
  'axes',
  'shields',
  'armor',
  'wagon',
  'siege_weapons',
  'jewelry',
  'spear',
  'horses',
  'pitchforks',
  'gold_cost'
];

let currentSession = null;

document.addEventListener("DOMContentLoaded", async () => {
  const {
    data: { session }
  } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  currentSession = session;

  // ✅ authGuard.js protects this page → no duplicate session checks
  // ✅ Initial load
  await loadProjects();
  setInterval(loadProjects, 30000);

  // ✅ Bind tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document
        .querySelectorAll('.tab-btn')
        .forEach(b => b.classList.remove('active'));

      document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
        tab.classList.remove('active');
      });

      btn.classList.add('active');
      const targetId = btn.dataset.tab;
      const target = document.getElementById(targetId);
      target.classList.remove('hidden');
      target.classList.add('active');
    });
  });
});

// ✅ Load Projects
async function loadProjects() {
  const availableList = document.getElementById('available-projects-list');
  const activeList = document.getElementById('active-projects-list');
  const powerScoreContainer = document.getElementById('power-score');

  if (!availableList || !activeList || !powerScoreContainer) return;

  availableList.innerHTML = "<p>Loading available projects...</p>";
  activeList.innerHTML = "<p>Loading active projects...</p>";
  powerScoreContainer.innerHTML = "<p>Loading power score...</p>";

  try {
    // ✅ Fetch user + kingdom resources
    const { data: { user } } = await supabase.auth.getUser();

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const kingdomId = userData.kingdom_id;

    const { data: resourcesData, error: resourcesError } = await supabase
      .from('kingdom_resources')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .single();

    if (resourcesError) throw resourcesError;

    // ✅ Fetch project catalogue
    const { data: catalogueData, error: catalogueError } = await supabase
      .from('project_player_catalogue')
      .select('*')
      .eq('is_active', true);

    const filteredCatalogue = (catalogueData || []).filter(
      p => !p.expires_at || new Date(p.expires_at) > new Date()
    );

    if (catalogueError) throw catalogueError;

    // ✅ Fetch player active projects
    const { data: playerProjectsData, error: playerProjectsError } = await supabase
      .from('projects_player')
      .select('*')
      .eq('kingdom_id', kingdomId);

    if (playerProjectsError) throw playerProjectsError;

    // ✅ Calculate power score
    const powerScore = playerProjectsData.reduce((score, project) => score + (project.power_score || 0), 0);
    powerScoreContainer.innerHTML = `<strong>Power Score:</strong> ${powerScore}`;

    // ✅ Separate active project codes
    const activeProjectCodes = playerProjectsData.map(p => p.project_code);

    // ✅ Render available projects
    availableList.innerHTML = "";
    filteredCatalogue.forEach(project => {
      const isActive = activeProjectCodes.includes(project.project_code);
      const canAfford = hasSufficientResources(resourcesData, project);

      const card = document.createElement("div");
      card.classList.add("project-card");

      card.innerHTML = `
        <h3>${escapeHTML(project.name)}</h3>
        <p>${escapeHTML(project.description)}</p>
        <p class="category">${escapeHTML(project.category || "")}</p>
        <p>${escapeHTML(project.effect_summary || "")}</p>
        <p>Cost: ${formatCostFromColumns(project)}</p>
        <p>Build Time: ${formatTime(project.build_time_seconds || 0)}</p>
        ${project.project_duration_seconds ? `<p>Duration: ${formatTime(project.project_duration_seconds)}</p>` : ''}
        <p>Power Score: ${project.power_score}</p>
        <button class="action-btn start-project-btn" data-code="${project.project_code}" ${isActive || !canAfford ? "disabled" : ""}>
          ${isActive ? "Already Active" : canAfford ? "Start Project" : "Insufficient Resources"}
        </button>
      `;

      availableList.appendChild(card);
    });

    // ✅ Bind start project buttons
    document.querySelectorAll(".start-project-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const projectCode = btn.dataset.code;
        if (!confirm(`Start project "${projectCode}"?`)) return;

        try {
          const res = await fetch("/api/projects/start", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${currentSession.access_token}`,
              "X-User-ID": currentSession.user.id
            },
            body: JSON.stringify({ project_code: projectCode })
          });

          const result = await res.json();

          if (!res.ok) throw new Error(result.error || "Failed to start project.");

          alert(result.message || "Project started!");
          await loadProjects(); // Refresh

        } catch (err) {
          console.error("❌ Error starting project:", err);
          alert("Failed to start project.");
        }
      });
    });

    // ✅ Render active projects
    activeList.innerHTML = "";

    if (playerProjectsData.length === 0) {
      activeList.innerHTML = "<p>No active projects.</p>";
      return;
    }

    playerProjectsData.forEach(activeProject => {
      const projectDef = filteredCatalogue.find(p => p.project_code === activeProject.project_code);

      const remainingTime = Math.max(0, Math.floor((new Date(activeProject.ends_at).getTime() - Date.now()) / 1000));
      const totalTime = Math.max(1, Math.floor((new Date(activeProject.ends_at).getTime() - new Date(activeProject.starts_at).getTime()) / 1000));
      const progressPercent = Math.min(100, Math.floor(((totalTime - remainingTime) / totalTime) * 100));

      const card = document.createElement("div");
      card.classList.add("project-card");

      card.innerHTML = `
        <h3>${escapeHTML(projectDef?.name || activeProject.project_code)}</h3>
        <p>${escapeHTML(projectDef?.description || "")}</p>
        <p>Power Score: ${activeProject.power_score}</p>
        <p>Time Remaining: <span class="countdown" data-ends-at="${activeProject.ends_at}">${formatTime(remainingTime)}</span></p>
        <div class="progress-bar"><div class="progress-bar-fill" data-width="${progressPercent}"></div></div>
      `;

      activeList.appendChild(card);
    });

    // ✅ Start countdown timer
    startCountdowns();

  } catch (err) {
    console.error("❌ Error loading projects:", err);
    availableList.innerHTML = "<p>Failed to load available projects.</p>";
    activeList.innerHTML = "<p>Failed to load active projects.</p>";
    powerScoreContainer.innerHTML = "<p>Failed to load power score.</p>";
  }
}

// ✅ Check if player has enough resources
function hasSufficientResources(resources, project) {
  const costs = {};
  RESOURCE_KEYS.forEach(k => {
    const val = project[k];
    if (typeof val === 'number' && val > 0) {
      const key = k.replace(/_cost$/, '');
      costs[key] = val;
    }
  });
  return Object.entries(costs).every(([res, amt]) => (resources[res] || 0) >= amt);
}

// ✅ Format cost object
function formatCostFromColumns(project) {
  const parts = [];
  RESOURCE_KEYS.forEach(k => {
    const val = project[k];
    if (typeof val === 'number' && val > 0) {
      const key = k.replace(/_cost$/, '');
      parts.push(`${val} ${escapeHTML(key)}`);
    }
  });
  return parts.join(', ') || 'None';
}

// ✅ Start countdown timers
function startCountdowns() {
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

// ✅ Format time
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  return `${h}h ${m}m ${s}s`;
}

// ✅ Basic HTML escape
