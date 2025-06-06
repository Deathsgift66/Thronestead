/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_projects.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ✅ Auth Guard and Logout Enforcement
(async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return window.location.href = 'login.html';

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await supabase.auth.signOut();
      window.location.href = 'login.html';
    });
  }
})();

// ✅ Load all components on DOM Ready
document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadProjects();
    await loadContributors();
    await loadNotifications();

    // Button hooks
    document.getElementById('start-new-project').addEventListener('click', startNewProject);
    document.getElementById('view-all-projects').addEventListener('click', viewAllProjects);

  } catch (error) {
    console.error('❌ Error initializing Alliance Projects Dashboard:', error);
    alert('Unable to load Alliance Projects Dashboard.');
  }
});

// ✅ Load Active Projects
async function loadProjects() {
  const container = document.getElementById('active-projects');
  container.innerHTML = '<p>Loading projects...</p>';

  try {
    const response = await fetch('/api/alliance-projects');
    if (!response.ok) throw new Error('Failed to fetch project data');

    const data = await response.json();
    renderProjects(data.projects);

  } catch (err) {
    console.error('❌ Error loading projects:', err);
    container.innerHTML = '<p>Failed to load projects.</p>';
  }
}

function renderProjects(projects) {
  const container = document.getElementById('active-projects');
  container.innerHTML = '';

  if (!projects || projects.length === 0) {
    container.innerHTML = '<p>No active projects at this time.</p>';
    return;
  }

  projects.forEach(project => {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.innerHTML = `
      <h4>${project.name}</h4>
      <p>Status: ${project.status}</p>
      <div class="progress-bar">
        <progress value="${project.completion}" max="100"></progress>
        <span>${project.completion}%</span>
      </div>
      <div class="project-actions">
        <button class="action-btn" data-action="start" data-id="${project.id}">▶️ Start</button>
        <button class="action-btn" data-action="update" data-id="${project.id}">🔄 Update</button>
      </div>
    `;
    container.appendChild(card);
  });

  attachProjectListeners();
}

// ✅ Attach Listeners for Dynamic Action Buttons
function attachProjectListeners() {
  document.querySelectorAll('button[data-action]').forEach(btn => {
    const action = btn.getAttribute('data-action');
    const id = btn.getAttribute('data-id');

    if (action === 'start') {
      btn.addEventListener('click', () => startProject(id));
    } else if (action === 'update') {
      btn.addEventListener('click', () => updateProject(id));
    }
  });
}

// ✅ Start a Project
async function startProject(projectId) {
  try {
    const res = await fetch('/api/alliance-projects/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId })
    });

    const result = await res.json();
    if (!res.ok) throw new Error(result.error || 'Unknown error');

    alert('✅ Project successfully started.');
    loadProjects();

  } catch (err) {
    console.error('❌ Start project error:', err);
    alert('Failed to start project.');
  }
}

// ✅ Update a Project
async function updateProject(projectId) {
  try {
    const res = await fetch('/api/alliance-projects/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId })
    });

    const result = await res.json();
    if (!res.ok) throw new Error(result.error || 'Unknown error');

    alert('✅ Project successfully updated.');
    loadProjects();

  } catch (err) {
    console.error('❌ Update project error:', err);
    alert('Failed to update project.');
  }
}

// ✅ Load Contributors
async function loadContributors() {
  const container = document.getElementById('project-contributors');
  container.innerHTML = '<p>Loading contributors...</p>';

  try {
    const response = await fetch('/api/alliance-projects/contributors');
    if (!response.ok) throw new Error('Failed to fetch contributors');

    const data = await response.json();
    renderContributors(data.contributors);

  } catch (err) {
    console.error('❌ Error loading contributors:', err);
    container.innerHTML = '<p>Failed to load contributors.</p>';
  }
}

function renderContributors(contributors) {
  const container = document.getElementById('project-contributors');
  container.innerHTML = '';

  if (!contributors || contributors.length === 0) {
    container.innerHTML = '<p>No contributors yet.</p>';
    return;
  }

  const list = document.createElement('ul');
  contributors.forEach(contributor => {
    const li = document.createElement('li');
    li.textContent = `${contributor.name}: ${contributor.contribution}`;
    list.appendChild(li);
  });

  container.appendChild(list);
}

// ✅ Load Notifications
async function loadNotifications() {
  const container = document.getElementById('project-notifications');
  container.innerHTML = '<p>Loading notifications...</p>';

  try {
    const response = await fetch('/api/alliance-projects/notifications');
    if (!response.ok) throw new Error('Failed to fetch notifications');

    const data = await response.json();
    renderNotifications(data.notifications);

  } catch (err) {
    console.error('❌ Error loading notifications:', err);
    container.innerHTML = '<p>Failed to load notifications.</p>';
  }
}

function renderNotifications(notifications) {
  const container = document.getElementById('project-notifications');
  container.innerHTML = '';

  if (!notifications || notifications.length === 0) {
    container.innerHTML = '<p>No project alerts at this time.</p>';
    return;
  }

  notifications.forEach(note => {
    const div = document.createElement('div');
    div.className = 'notification-item';
    div.innerHTML = `
      <p><strong>${note.title}</strong></p>
      <p>${note.message}</p>
      <p class="timestamp">${new Date(note.timestamp).toLocaleString()}</p>
    `;
    container.appendChild(div);
  });
}

// ✅ Button: Start New Project
function startNewProject() {
  alert('🚧 Start New Project — feature under development.');
  // In full version: Open modal to select available projects
}

// ✅ Button: View All Projects
function viewAllProjects() {
  alert('🚧 View All Projects — feature under development.');
  // In full version: Navigate to full Alliance Project Catalog page
}
