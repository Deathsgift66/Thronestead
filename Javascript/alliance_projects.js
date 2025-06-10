import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  setupTabs();
  await loadAllLists();
});

function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
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

async function loadAvailable() {
  const container = document.getElementById('available-projects-list');
  container.innerHTML = '<p>Loading...</p>';
  try {
    const { allianceId } = await getAllianceInfo();
    const res = await fetch(`/api/alliance-projects/available?alliance_id=${allianceId}`);
    const json = await res.json();
    renderAvailable(json.projects || []);
  } catch (err) {
    console.error('loadAvailable', err);
    container.innerHTML = '<p>Failed to load.</p>';
  }
}

function renderAvailable(list) {
  const container = document.getElementById('available-projects-list');
  container.innerHTML = '';
  if (list.length === 0) {
    container.innerHTML = '<p>No projects available.</p>';
    return;
  }
  list.forEach(p => {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.innerHTML = `
      <h3>${escapeHTML(p.project_name)}</h3>
      <p>${escapeHTML(p.description || '')}</p>
      <p>Build Time: ${formatTime(p.build_time_seconds || 0)}</p>
      <button class="action-btn start-btn" data-key="${p.project_code}">Start</button>
    `;
    container.appendChild(card);
  });
  document.querySelectorAll('.start-btn').forEach(btn => {
    btn.addEventListener('click', () => startProject(btn.dataset.key));
  });
}

async function loadInProgress() {
  const container = document.getElementById('in-progress-projects-list');
  container.innerHTML = '<p>Loading...</p>';
  try {
    const { allianceId } = await getAllianceInfo();
    const res = await fetch(`/api/alliance-projects/in-progress?alliance_id=${allianceId}`);
    const json = await res.json();
    renderInProgress(json.projects || []);
  } catch (err) {
    console.error('loadInProgress', err);
    container.innerHTML = '<p>Failed to load.</p>';
  }
}

function renderInProgress(list) {
  const container = document.getElementById('in-progress-projects-list');
  container.innerHTML = '';
  if (list.length === 0) {
    container.innerHTML = '<p>No active projects.</p>';
    return;
  }
  list.forEach(p => {
    const percent = p.progress || 0;
    const card = document.createElement('div');
    card.className = 'project-card';
    card.innerHTML = `
      <h3>${escapeHTML(p.project_key)}</h3>
      <div class="progress-bar">
        <div class="progress-bar-fill" style="width:${percent}%"></div>
      </div>
      <p>${percent}% complete</p>
    `;
    container.appendChild(card);
  });
}

async function loadCompleted() {
  const container = document.getElementById('completed-projects-list');
  container.innerHTML = '<p>Loading...</p>';
  try {
    const { allianceId } = await getAllianceInfo();
    const res = await fetch(`/api/alliance-projects/built?alliance_id=${allianceId}`);
    const json = await res.json();
    renderCompleted(json.projects || []);
  } catch (err) {
    console.error('loadCompleted', err);
    container.innerHTML = '<p>Failed to load.</p>';
  }
}

function renderCompleted(list) {
  const container = document.getElementById('completed-projects-list');
  container.innerHTML = '';
  if (list.length === 0) {
    container.innerHTML = '<p>No completed projects.</p>';
    return;
  }
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

async function loadCatalogue() {
  const container = document.getElementById('catalogue-projects-list');
  container.innerHTML = '<p>Loading...</p>';
  try {
    const res = await fetch('/api/alliance-projects/catalogue');
    const json = await res.json();
    renderCatalogue(json.projects || []);
  } catch (err) {
    console.error('loadCatalogue', err);
    container.innerHTML = '<p>Failed to load.</p>';
  }
}

function renderCatalogue(list) {
  const container = document.getElementById('catalogue-projects-list');
  container.innerHTML = '';
  if (list.length === 0) {
    container.innerHTML = '<p>No projects found.</p>';
    return;
  }
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

async function startProject(projectKey) {
  try {
    const { userId } = await getAllianceInfo();
    const res = await fetch('/api/alliance-projects/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_key: projectKey, user_id: userId })
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'error');
    await loadAllLists();
  } catch (err) {
    console.error('startProject', err);
    alert('Failed to start project');
  }
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

function escapeHTML(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
