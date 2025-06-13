// Project Name: Kingmakers Rise©
// File Name: alliance_projects.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

const RESOURCE_KEYS = [
  'wood', 'stone', 'iron_ore', 'gold', 'gems', 'food', 'coal', 'livestock',
  'clay', 'flax', 'tools', 'wood_planks', 'refined_stone', 'iron_ingots',
  'charcoal', 'leather', 'arrows', 'swords', 'axes', 'shields', 'armour',
  'wagon', 'siege_weapons', 'jewelry', 'spear', 'horses', 'pitchforks',
  'wood_cost', 'stone_cost', 'iron_cost', 'gold_cost', 'wood_plan_cost', 'iron_ingot_cost'
];

document.addEventListener('DOMContentLoaded', async () => {
  setupTabs();
  await loadAllLists();
  setInterval(loadAllLists, 30000);
});

function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab)?.classList.add('active');
    });
  });
}

async function loadAllLists() {
  await Promise.all([
    loadAvailable(),
    loadInProgress(),
    loadCompleted(),
    loadCatalogue()
  ]);
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
    const res = await fetch(`/api/alliance-projects/available?alliance_id=${allianceId}`);
    const json = await res.json();
    renderAvailable(json.projects || []);
  } catch (err) {
    console.error('loadAvailable', err);
    container.innerHTML = '<p>Failed to load available projects.</p>';
  }
}

function renderAvailable(list) {
  const container = document.getElementById('available-projects-list');
  container.innerHTML = list.length ? '' : '<p>No projects available.</p>';
  list.forEach(p => {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.innerHTML = `
      <h3>${escapeHTML(p.project_name)}</h3>
      <p>${escapeHTML(p.description || '')}</p>
      <p>Costs: ${formatCostFromColumns(p)}</p>
      <p>Build Time: ${formatTime(p.build_time_seconds || 0)}</p>
      <button class="action-btn start-btn" data-key="${p.project_code}">Start</button>
    `;
    container.appendChild(card);
  });

  container.querySelectorAll('.start-btn').forEach(btn => {
    btn.addEventListener('click', () => startProject(btn.dataset.key));
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
    const res = await fetch(`/api/alliance-projects/in-progress?alliance_id=${allianceId}`);
    const json = await res.json();
    renderInProgress(json.projects || []);
  } catch (err) {
    console.error('loadInProgress', err);
    container.innerHTML = '<p>Failed to load in-progress projects.</p>';
  }
}

function renderInProgress(list) {
  const container = document.getElementById('in-progress-projects-list');
  container.innerHTML = list.length ? '' : '<p>No active projects.</p>';
  list.forEach(p => {
    const percent = p.progress || 0;
    const card = document.createElement('div');
    card.className = 'project-card';
    const eta = formatTime(Math.max(0, Math.floor((new Date(p.expected_end) - Date.now()) / 1000)));
    card.innerHTML = `
      <h3>${escapeHTML(p.project_key)}</h3>
      <div class="progress-bar"><div class="progress-bar-fill" style="width:${percent}%"></div></div>
      <p>${percent}% complete - ETA ${eta}</p>
      <ul class="contrib-list">Loading...</ul>
    `;
    container.appendChild(card);
    loadLeaderboard(p.project_key, card.querySelector('.contrib-list'));
  });
}

async function loadLeaderboard(key, element) {
  try {
    const res = await fetch(`/api/alliance-projects/leaderboard?project_key=${key}`);
    const data = await res.json();
    const list = data.leaderboard || [];
    element.innerHTML = list.length
      ? ''
      : '<li>No contributions yet.</li>';

    list.forEach(r => {
      const li = document.createElement('li');
      li.textContent = `${escapeHTML(r.player_name)}: ${r.total}`;
      element.appendChild(li);
    });
  } catch (err) {
    console.error('leaderboard', err);
    element.innerHTML = '<li>Failed to load leaderboard.</li>';
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
    const res = await fetch(`/api/alliance-projects/built?alliance_id=${allianceId}`);
    const json = await res.json();
    renderCompleted(json.projects || []);
  } catch (err) {
    console.error('loadCompleted', err);
    container.innerHTML = '<p>Failed to load completed projects.</p>';
  }
}

function renderCompleted(list) {
  const container = document.getElementById('completed-projects-list');
  container.innerHTML = list.length ? '' : '<p>No completed projects.</p>';
  list.forEach(p => {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.innerHTML = `
      <h3>${escapeHTML(p.name || p.project_key)}</h3>
      <p>Completed on: ${new Date(p.end_time).toLocaleString()}</p>
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
    const res = await fetch('/api/alliance-projects/catalogue');
    const json = await res.json();
    renderCatalogue(json.projects || []);
  } catch (err) {
    console.error('loadCatalogue', err);
    container.innerHTML = '<p>Failed to load project catalogue.</p>';
  }
}

function renderCatalogue(list) {
  const container = document.getElementById('catalogue-projects-list');
  container.innerHTML = list.length ? '' : '<p>No projects found.</p>';
  list.forEach(p => {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.innerHTML = `
      <h3>${escapeHTML(p.project_name)}</h3>
      <p>${escapeHTML(p.description || '')}</p>
      <p>Category: ${escapeHTML(p.category || '')}</p>
    `;
    container.appendChild(card);
  });
}

// ----------------------------
// ➕ Start a Project
// ----------------------------
async function startProject(projectKey) {
  try {
    const { userId } = await getAllianceInfo();
    const res = await fetch('/api/alliance-projects/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_key: projectKey, user_id: userId })
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Unknown error');
    await loadAllLists();
  } catch (err) {
    console.error('startProject', err);
    alert('❌ Failed to start project.');
  }
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

function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
