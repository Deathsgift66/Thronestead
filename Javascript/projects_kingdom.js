/*
Project Name: Kingmakers Rise Frontend
File Name: projects_kingdom.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session checks
  // ✅ Initial load
  await loadProjects();

  // ✅ Bind tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));

      btn.classList.add('active');
      const targetId = btn.dataset.tab;
      document.getElementById(targetId).classList.remove('hidden');
    });
  });
});

// ✅ Load Projects
async function loadProjects() {
  const availableList = document.getElementById('available-projects-list');
  const activeList = document.getElementById('active-projects-list');
  const powerScoreContainer = document.getElementById('power-score');

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
      .select('*');

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
    catalogueData.forEach(project => {
      const isActive = activeProjectCodes.includes(project.project_code);
      const canAfford = hasSufficientResources(resourcesData, project);

      const card = document.createElement("div");
      card.classList.add("project-card");

      card.innerHTML = `
        <h3>${escapeHTML(project.name)}</h3>
        <p>${escapeHTML(project.description)}</p>
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
          const res = await fetch("/api/kingdom/start_project", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
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
      const projectDef = catalogueData.find(p => p.project_code === activeProject.project_code);

      const remainingTime = Math.max(0, Math.floor((new Date(activeProject.ends_at).getTime() - Date.now()) / 1000));

      const card = document.createElement("div");
      card.classList.add("project-card");

      card.innerHTML = `
        <h3>${escapeHTML(projectDef?.name || activeProject.project_code)}</h3>
        <p>${escapeHTML(projectDef?.description || "")}</p>
        <p>Power Score: ${activeProject.power_score}</p>
        <p>Time Remaining: <span class="countdown" data-ends-at="${activeProject.ends_at}">${formatTime(remainingTime)}</span></p>
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
  const costFields = Object.keys(resources).filter(key => project[key] > 0);

  return costFields.every(resource => resources[resource] >= project[resource]);
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
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
