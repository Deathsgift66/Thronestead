// Project Name: Thronestead©
// File Name: alliance_projects.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { escapeHTML, openModal } from './utils.js';

const RESOURCE_KEYS = [
  'wood', 'stone', 'iron_ore', 'gold', 'gems', 'food', 'coal', 'livestock',
  'clay', 'flax', 'tools', 'wood_planks', 'refined_stone', 'iron_ingots',
  'charcoal', 'leather', 'arrows', 'swords', 'axes', 'shields', 'armor',
  'wagon', 'siege_weapons', 'jewelry', 'spear', 'horses', 'pitchforks',
  'wood_cost', 'stone_cost', 'iron_cost', 'gold_cost', 'wood_plan_cost', 'iron_ingot_cost'
];

let projectChannel = null;

document.addEventListener('DOMContentLoaded', async () => {
  setupTabs();
  await loadAllLists();
  await setupRealtimeProjects();
  setInterval(loadAllLists, 30000); // Auto-refresh
  window.addEventListener('beforeunload', () => {
    if (projectChannel) supabase.removeChannel(projectChannel);
  });
});

// ----------------------------
// 🔁 Realtime Sync
// ----------------------------
async function setupRealtimeProjects() {
  const { allianceId } = await getAllianceInfo();
  if (!allianceId) return;

  if (projectChannel) supabase.removeChannel(projectChannel);

  projectChannel = supabase
    .channel(`realtime:alliance_projects_${allianceId}`)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'alliance_projects',
      filter: `alliance_id=eq.${allianceId}`
    }, () => loadAllLists())
    .subscribe();
}

// ----------------------------
// 🧭 Tab UI
// ----------------------------
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab)?.classList.add('active');
    });
    btn.addEventListener('keydown', e => {
      if (['ArrowLeft', 'ArrowRight'].includes(e.key)) {
        const tabs = Array.from(document.querySelectorAll('.tab-btn'));
        const idx = tabs.indexOf(document.activeElement);
        const next = e.key === 'ArrowLeft'
          ? (idx - 1 + tabs.length) % tabs.length
          : (idx + 1) % tabs.length;
        tabs[next].focus();
        tabs[next].click();
      }
    });
  });
}

// ----------------------------
// 📥 Load All Tabs
// ----------------------------
async function loadAllLists() {
  await Promise.all([
    loadAvailable(),
    loadInProgress(),
    loadCompleted(),
    loadCatalogue()
  ]);
  const live = document.getElementById('project-updates');
  if (live) live.textContent = 'Project data updated.';
}

async function getAllianceInfo() {
  const { data: { user } } = await supabase.auth.getUser();
  const { data, error } = await supabase
    .from('users')
    .select('alliance_id')
    .eq('user_id', user.id)
    .single();
  if (error) throw error;
  return { userId: user.id, allianceId: data.alliance_id };
}

// ----------------------------
// ✅ Available Projects
// ----------------------------
async function loadAvailable() {
  const container = document.getElementById('available-projects-list');
  if (!container) return;
  container.innerHTML = '<p>Loading...</p>';

  try {
    const { allianceId } = await getAllianceInfo();
    const res = await fetch(`/api/alliance/projects/available?alliance_id=${allianceId}`);
    const json = await res.json();
    renderAvailable(json.projects || []);
  } catch (err) {
    if (process.env.NODE_ENV === 'development') {
      console.error('loadAvailable', err);
    }
    container.innerHTML = '<p>Failed to load available projects.</p>';
  }
}

function renderAvailable(list) {
  const container = document.getElementById('available-projects-list');
  container.innerHTML = list.length
    ? ''
    : '<p class="empty-state">No projects found in this category.</p>';

  if (!window.user) {
    console.warn('⚠️ No user context found. Permissions may be unavailable.');
  }
  const canStart = window.user?.permissions?.includes('can_manage_projects');
  list.forEach(p => {
    const card = document.createElement('article');
    card.className = 'project-card';
    card.setAttribute('role', 'region');
    card.setAttribute('aria-label', `Project: ${p.project_name}`);
    card.innerHTML = `
      <h3>${escapeHTML(p.project_name)}</h3>
      <p>${escapeHTML(p.description || '')}</p>
      <p>Costs: ${formatCostFromColumns(p)}</p>
      <p>Build Time: ${formatTime(p.build_time_seconds || 0)}</p>
      ${canStart ? `<button class="btn build-btn" data-project="${p.project_key}">Start Project</button>` : ''}
    `;
    container.appendChild(card);
  });

  container.querySelectorAll('.build-btn').forEach(btn => {
    btn.addEventListener('click', () => startProject(btn.dataset.project));
  });
}

// ----------------------------
// 🛠 In Progress Projects
// ----------------------------
async function loadInProgress() {
  const container = document.getElementById('in-progress-projects-list');
  if (!container) return;
  container.innerHTML = '<p>Loading...</p>';

  try {
    const { allianceId } = await getAllianceInfo();
    const res = await fetch(`/api/alliance/projects/in_progress?alliance_id=${allianceId}`);
    const json = await res.json();
    renderInProgress(json.projects || []);
  } catch (err) {
    if (process.env.NODE_ENV === 'development') {
      console.error('loadInProgress', err);
    }
    container.innerHTML = '<p>Failed to load in-progress projects.</p>';
  }
}

function renderInProgress(list) {
  const container = document.getElementById('in-progress-projects-list');
  container.innerHTML = list.length
    ? ''
    : '<p class="empty-state">No projects found in this category.</p>';

  list.forEach(p => {
    const percent = p.progress || 0;
    const card = document.createElement('article');
    card.className = 'project-card';
    card.setAttribute('role', 'region');
    card.setAttribute('aria-label', `Project: ${p.project_key}`);
    const eta = formatTime(Math.max(0, Math.floor((new Date(p.expected_end) - Date.now()) / 1000)));

    card.innerHTML = `
      <h3>${escapeHTML(p.project_key)}</h3>
      <progress value="${percent}" max="100"></progress>
      <span>${percent}% - ETA ${eta}</span>
      <div class="contrib-summary">Loading...</div>
    `;

    container.appendChild(card);
    loadContributions(p.project_key, card.querySelector('.contrib-summary'));
  });
}

async function loadContributions(key, element) {
  try {
    const res = await fetch(`/api/alliance/projects/contributions?project_key=${key}`);
    const data = await res.json();
    const list = data.contributions || [];
    const totalContributors = data.totalContributors || list.length;

    if (!list.length) {
      element.innerHTML = '<p class="empty-state">No contributions yet.</p>';
      return;
    }

    const total = list.reduce((sum, r) => sum + r.amount, 0) || 1;
    element.innerHTML = '';

    list.slice(0, 3).forEach(r => {
      const div = document.createElement('div');
      div.className = 'contrib-entry';
      div.innerHTML = `
        <span>${escapeHTML(r.player_name)}</span>
        <div class="contrib-bar"><div class="contrib-bar-fill" data-width="${(r.amount / total) * 100}"></div></div>
      `;
      const fill = div.querySelector('.contrib-bar-fill');
      fill.style.width = `${(r.amount / total) * 100}%`;
      element.appendChild(div);
    });

    if (totalContributors > 3) {
      const btn = document.createElement('button');
      btn.className = 'btn view-all-btn';
      btn.textContent = 'View All';
      btn.addEventListener('click', () => openContribModal(key));
      element.appendChild(btn);
    }
  } catch (err) {
    if (process.env.NODE_ENV === 'development') {
      console.error('contributions', err);
    }
    element.innerHTML = '<p class="empty-state">Failed to load.</p>';
  }
}

// ----------------------------
// 🏁 Completed Projects
// ----------------------------
async function loadCompleted() {
  const container = document.getElementById('completed-projects-list');
  if (!container) return;
  container.innerHTML = '<p>Loading...</p>';

  try {
    const { allianceId } = await getAllianceInfo();
    const res = await fetch(`/api/alliance/projects/completed?alliance_id=${allianceId}`);
    const json = await res.json();
    renderCompleted(json.projects || []);
  } catch (err) {
    if (process.env.NODE_ENV === 'development') {
      console.error('loadCompleted', err);
    }
    container.innerHTML = '<p>Failed to load completed projects.</p>';
  }
}

function renderCompleted(list) {
  const container = document.getElementById('completed-projects-list');
  container.innerHTML = list.length
    ? ''
    : '<p class="empty-state">No projects found in this category.</p>';

  list.forEach(p => {
    const card = document.createElement('article');
    card.className = 'project-card completed-project';
    card.setAttribute('role', 'region');
    card.setAttribute('aria-label', `Project: ${p.name || p.project_key}`);
    const builtBy = p.built_by ? ` by ${escapeHTML(p.built_by)}` : '';
    card.innerHTML = `
      <h3>${escapeHTML(p.name || p.project_key)}</h3>
      <p>Completed on ${new Date(p.end_time).toLocaleDateString()}${builtBy}</p>
    `;
    container.appendChild(card);
  });
}

// ----------------------------
// 📖 Project Catalogue
// ----------------------------
async function loadCatalogue() {
  const container = document.getElementById('catalogue-projects-list');
  if (!container) return;
  container.innerHTML = '<p>Loading...</p>';

  try {
    const res = await fetch('/api/alliance/projects/catalogue');
    const json = await res.json();
    renderCatalogue(json.projects || []);
  } catch (err) {
    if (process.env.NODE_ENV === 'development') {
      console.error('loadCatalogue', err);
    }
    container.innerHTML = '<p>Failed to load project catalogue.</p>';
  }
}

function renderCatalogue(list) {
  const container = document.getElementById('catalogue-projects-list');
  container.innerHTML = list.length
    ? ''
    : '<p class="empty-state">No projects found in this category.</p>';

  list.forEach(p => {
    const card = document.createElement('article');
    card.className = 'project-card';
    card.setAttribute('role', 'region');
    card.setAttribute('aria-label', `Project: ${p.project_name}`);
    const status = p.status || 'Available';
    const statusIcon = status === 'Completed' ? '✅' : status === 'Available' ? '🔓' : '🔒';

    card.innerHTML = `
      <h3>${escapeHTML(p.project_name)} ${statusIcon}</h3>
      <p>${escapeHTML(p.description || '')}</p>
      <p>Category: ${escapeHTML(p.category || '')}</p>
    `;

    if (status === 'Locked') card.classList.add('locked');
    container.appendChild(card);
  });
}

// ----------------------------
// ➕ Start a Project
// ----------------------------
async function startProject(projectKey) {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/alliance/projects/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': user.id
      },
      body: JSON.stringify({ project_key: projectKey })
    });

    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Unknown error');

    await loadAllLists();
    const live = document.getElementById('project-updates');
    if (live) live.textContent = 'Project started successfully.';
  } catch (err) {
    if (process.env.NODE_ENV === 'development') {
      console.error('startProject', err);
    }
    alert('❌ Failed to start project.');
  }
}

async function openContribModal(key) {
  const modal = document.getElementById('contrib-modal');
  if (!modal) return;
  const title = modal.querySelector('.modal-title');
  const listEl = modal.querySelector('.modal-list');
  if (title) title.textContent = `Contributors for ${key}`;
  if (listEl) listEl.innerHTML = 'Loading...';
  try {
    const res = await fetch(`/api/alliance/projects/contributions?project_key=${key}`);
    const data = await res.json();
    const list = data.contributions || [];
    listEl.innerHTML = list
      .map(r => `<div>${escapeHTML(r.player_name)} - ${r.amount}</div>`)
      .join('') || '<p class="empty-state">No contributions.</p>';
  } catch (err) {
    if (process.env.NODE_ENV === 'development') {
      console.error('openContribModal', err);
    }
    if (listEl) listEl.innerHTML = '<p class="empty-state">Failed to load.</p>';
  }
  openModal(modal);
}

// ----------------------------
// 🧮 Utility
// ----------------------------
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

function formatCostFromColumns(obj) {
  return RESOURCE_KEYS
    .filter(key => typeof obj[key] === 'number' && obj[key] > 0)
    .map(key => `${obj[key]} ${escapeHTML(key.replace(/_cost$/, ''))}`)
    .join(', ') || 'N/A';
}
