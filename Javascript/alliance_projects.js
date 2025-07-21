// Project Name: Thronestead©
// File Name: alliance_projects.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { initCsrf, getCsrfToken, rotateCsrfToken } from './security/csrf.js';

initCsrf();
setInterval(rotateCsrfToken, 15 * 60 * 1000);

const DEFAULT_BANNER = '/Assets/banner.png';

function logError(context, err) {
  if (process.env.NODE_ENV === 'development') {
    console.error(`❌ ${context}`, err);
  } else {
    try {
      supabase.from('client_errors').insert({
        context,
        message: err?.message || String(err),
        stack: err?.stack || null
      });
    } catch (e) {
      console.error('error reporting failed', e);
    }
  }
}


async function applyAllianceAppearance() {
  try {
    const { data: { session } = {} } = await supabase.auth.getSession();
    const userId = session?.user?.id;
    if (!userId) {
      window.location.href = 'login.html';
      return;
    }

    const { alliance } = await authJsonFetch('/api/alliance-home/details', {
      headers: await authHeaders()
    });
    if (!alliance) return;

    const banner = alliance.banner || DEFAULT_BANNER;
    const emblem = alliance.emblem_url;

    const og = document.querySelector('meta[property="og:image"]');
    if (og) og.setAttribute('content', banner);

    document.querySelectorAll('.alliance-banner').forEach(img => {
      img.src = banner;
    });

    if (emblem) {
      document.querySelectorAll('.alliance-emblem').forEach(img => {
        img.src = emblem;
      });
    }

    document.querySelectorAll('.alliance-bg').forEach(el => {
      el.style.backgroundImage = `url(${banner})`;
      el.style.backgroundSize = 'cover';
      el.style.backgroundAttachment = 'fixed';
      el.style.backgroundRepeat = 'no-repeat';
      el.style.backgroundPosition = 'center';
    });

  } catch (err) {
    logError('Failed to apply alliance appearance', err);
    document.querySelectorAll('.alliance-banner').forEach(img => {
      img.src = DEFAULT_BANNER;
    });
  }
}

let userContext = JSON.parse(sessionStorage.getItem('userContext') || 'null');
async function loadUserContext() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const ctx = await authJsonFetch(`/api/player/context?user_id=${user.id}`);
      userContext = { ...(userContext || {}), ...ctx };
      sessionStorage.setItem('userContext', JSON.stringify(userContext));
    }
  } catch (err) {
    logError('Failed to load user context', err);
  }
}

import { renderProgressionBanner } from './progressionBanner.js';



import {
  escapeHTML,
  openModal,
  closeModal,
  authHeaders,
  authJsonFetch,
  debounce,
  formatDuration,
} from './utils.js';
import { RESOURCE_KEYS } from './resourceKeys.js';

let projectChannel = null;
const loadedTabs = { completed: false, catalogue: false };
let cachedAlliance = null;
let startingProject = false;
let availableData = [];
let completedData = [];
let catalogueData = [];
let contribList = [];
let contribPage = 0;
const CONTRIB_PAGE_SIZE = 50;
let realtimeRetries = 0;
const MAX_REALTIME_RETRIES = 5;

async function main() {
  renderProgressionBanner();
  await applyAllianceAppearance();
  await loadUserContext();
  setupTabs();
  await Promise.all([loadAvailable(), loadInProgress()]);
  await setupRealtimeProjects();
  setInterval(loadAllLists, 30000);
  window.addEventListener('beforeunload', async () => {
    if (projectChannel) await projectChannel.unsubscribe();
    projectChannel = null;
    sessionStorage.removeItem('completedProjects');
    sessionStorage.removeItem('catalogueProjects');
  });

  supabase.auth.onAuthStateChange(async () => {
    cachedAlliance = null;
    sessionStorage.removeItem('completedProjects');
    sessionStorage.removeItem('catalogueProjects');
    if (projectChannel) {
      await projectChannel.unsubscribe();
      projectChannel = null;
    }
    await setupRealtimeProjects();
  });

  document.addEventListener('keydown', e => {
    if (e.ctrlKey && ['ArrowLeft', 'ArrowRight'].includes(e.key) &&
        !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      const tabs = Array.from(document.querySelectorAll('.tab-btn'));
      const idx = tabs.findIndex(t => t.classList.contains('active'));
      const next = e.key === 'ArrowLeft'
        ? (idx - 1 + tabs.length) % tabs.length
        : (idx + 1) % tabs.length;
      tabs[next].focus();
      tabs[next].click();
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeContribModal();
  });

  const modal = document.getElementById('contrib-modal');
  modal?.addEventListener('click', e => {
    if (e.target === modal) closeContribModal();
  });
  document.getElementById('contrib-modal-close')?.addEventListener('click', closeContribModal);
}

document.addEventListener('DOMContentLoaded', main);

async function setupRealtimeProjects() {
  const { allianceId } = await getAllianceInfo();
  if (!allianceId) return;

  if (projectChannel) await projectChannel.unsubscribe();
  projectChannel = null;
  realtimeRetries = 0;

  projectChannel = supabase
    .channel(`realtime:alliance_projects_${allianceId}`)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'alliance_projects',
      filter: `alliance_id=eq.${allianceId}`
    }, () => loadAllLists())
    .on('error', err => {
      logError('realtime error', err);
      retryRealtime();
    })
    .on('close', retryRealtime)
    .subscribe();
}

function retryRealtime() {
  if (realtimeRetries >= MAX_REALTIME_RETRIES) return;
  const delay = Math.min(1000 * 2 ** realtimeRetries, 30000);
  realtimeRetries++;
  setTimeout(setupRealtimeProjects, delay);
}

const debouncedLoadCompleted = debounce(async () => {
  await loadCompleted();
  loadedTabs.completed = true;
}, 300);
const debouncedLoadCatalogue = debounce(async () => {
  await loadCatalogue();
  loadedTabs.catalogue = true;
}, 300);

function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('tabindex', '-1');
      });
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      btn.setAttribute('tabindex', '0');
      document.getElementById(btn.dataset.tab)?.classList.add('active');

      if (btn.dataset.tab === 'completed-tab' && !loadedTabs.completed) {
        debouncedLoadCompleted();
      } else if (btn.dataset.tab === 'catalogue-tab' && !loadedTabs.catalogue) {
        debouncedLoadCatalogue();
      }
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
  document.getElementById('available-sort')?.addEventListener('change', debounce(() => renderAvailable(availableData), 250));
  document.getElementById('completed-sort')?.addEventListener('change', debounce(() => renderCompleted(completedData), 250));
}

function setLiveMessage(msg) {
  const live = document.getElementById('project-updates');
  if (!live) return;
  live.textContent = msg;
  setTimeout(() => {
    if (live.textContent === msg) live.textContent = '';
  }, 3000);
}

async function loadAllLists() {
  const tasks = [loadAvailable(), loadInProgress()];
  if (loadedTabs.completed) tasks.push(loadCompleted());
  if (loadedTabs.catalogue) tasks.push(loadCatalogue());
  await Promise.all(tasks);
  setLiveMessage('Project data updated!');
}

async function getAllianceInfo(force = false) {
  if (cachedAlliance && !force) return cachedAlliance;
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.id || typeof user.id !== 'string') {
    window.location.href = 'login.html';
    throw new Error('User session lost or invalid.');
  }
  const { data, error } = await supabase
    .from('users')
    .select('alliance_id')
    .eq('user_id', user.id)
    .single();
  if (error) throw error;
  cachedAlliance = { userId: user.id, allianceId: data.alliance_id };
  return cachedAlliance;
}

async function loadAvailable() {
  const container = document.getElementById('available-projects-list');
  if (!container) return;
  renderSkeletons(container);

  try {
    const { allianceId } = await getAllianceInfo();
    const json = await authJsonFetch(`/api/alliance/projects/available?alliance_id=${allianceId}`);
    if (!json.projects) {
      container.innerHTML = '<p class="empty-state">No projects returned.</p>';
      availableData = [];
    } else {
      availableData = json.projects;
    }
    renderAvailable(availableData);
  } catch (err) {
    logError('loadAvailable', err);
    container.innerHTML = '<p>Failed to load available projects.</p>';
  }
}

function renderAvailable(list) {
  const container = document.getElementById('available-projects-list');
  const sort = document.getElementById('available-sort')?.value || 'name';
  const sorted = sortProjects(list, sort);
  container.innerHTML = sorted.length
    ? ''
    : '<p class="empty-state">No projects found in this category.</p>';

  availableData = list;

  if (!userContext) {
    console.warn('⚠️ No user context found. Permissions may be unavailable.');
  }
  const canStart = userContext?.permissions?.includes('can_manage_projects');
  sorted.forEach(p => {
    const card = document.createElement('article');
    card.className = 'project-card';
    card.setAttribute('role', 'region');
    card.setAttribute('aria-label', `Project: ${p.project_name}`);
    const cost = formatCostFromColumns(p);
    const costId = `cost-${p.project_key}`;
    const timeId = `time-${p.project_key}`;
    card.innerHTML = `
      <h3>${escapeHTML(p.project_name)}</h3>
      <p>${escapeHTML(p.description || '')}</p>
      <dl>
        <div><dt>Costs</dt><dd id="${costId}" class="project-cost" title="${cost}">${cost}</dd></div>
        <div><dt>Build Time</dt><dd id="${timeId}">${formatDuration(p.build_time_seconds || 0, { compact: true, instant: 'Instant' })}</dd></div>
      </dl>
      ${canStart ? `<button class="btn build-btn" data-project="${p.project_key}" aria-describedby="${costId} ${timeId}">Start Project</button>` : ''}
    `;
    container.appendChild(card);
  });

  container.querySelectorAll('.build-btn').forEach(btn => {
    btn.addEventListener('click', () => startProject(btn.dataset.project, btn));
  });
}

async function loadInProgress() {
  const container = document.getElementById('in-progress-projects-list');
  if (!container) return;
  renderSkeletons(container);

  try {
    const { allianceId } = await getAllianceInfo();
    const json = await authJsonFetch(`/api/alliance/projects/in_progress?alliance_id=${allianceId}`);
    renderInProgress(json.projects || []);
  } catch (err) {
    logError('loadInProgress', err);
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
    const title = p.project_name || p.project_key;
    card.setAttribute('aria-label', `Project: ${title}`);
    const eta = formatDuration(Math.max(0, Math.floor((new Date(p.expected_end) - Date.now()) / 1000)), { compact: true });

    card.innerHTML = `
      <h3>${escapeHTML(title)}</h3>
      <div class="progress-bar"><div class="progress-bar-fill" style="width:0%"></div></div>
      <span>${percent}% - ETA ${eta}</span>
      <div class="contrib-summary">Loading...</div>
    `;

    container.appendChild(card);
    const fill = card.querySelector('.progress-bar-fill');
    requestAnimationFrame(() => { fill.style.width = `${percent}%`; });
    loadContributions(p.project_key, card.querySelector('.contrib-summary'));
  });
}

async function loadContributions(key, element) {
  try {
    const data = await authJsonFetch(`/api/alliance/projects/contributions?project_key=${key}`);
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
    logError('contributions', err);
    element.innerHTML = '<p class="empty-state">Failed to load.</p>';
  }
}

async function loadCompleted() {
  const container = document.getElementById('completed-projects-list');
  if (!container) return;
  const cached = sessionStorage.getItem('completedProjects');
  if (cached) {
    completedData = JSON.parse(cached);
    renderCompleted(completedData);
  } else {
    renderSkeletons(container);
  }

  try {
    const { allianceId } = await getAllianceInfo();
    const json = await authJsonFetch(`/api/alliance/projects/completed?alliance_id=${allianceId}`);
    if (!json.projects) {
      container.innerHTML = '<p class="empty-state">No projects returned.</p>';
      completedData = [];
    } else {
      completedData = json.projects;
    }
    sessionStorage.setItem('completedProjects', JSON.stringify(completedData));
    renderCompleted(completedData);
  } catch (err) {
    logError('loadCompleted', err);
    container.innerHTML = '<p>Failed to load completed projects.</p>';
  }
}

function renderCompleted(list) {
  const container = document.getElementById('completed-projects-list');
  const sort = document.getElementById('completed-sort')?.value || 'name';
  const sorted = sortProjects(list, sort);
  container.innerHTML = sorted.length
    ? ''
    : '<p class="empty-state">No projects found in this category.</p>';

  completedData = list;

  sorted.forEach(p => {
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

async function loadCatalogue() {
  const container = document.getElementById('catalogue-projects-list');
  if (!container) return;
  const cached = sessionStorage.getItem('catalogueProjects');
  if (cached) {
    catalogueData = JSON.parse(cached);
    renderCatalogue(catalogueData);
  } else {
    renderSkeletons(container);
  }

  try {
    const json = await authJsonFetch('/api/alliance/projects/catalogue');
    if (!json.projects) {
      container.innerHTML = '<p class="empty-state">No projects returned.</p>';
      catalogueData = [];
    } else {
      catalogueData = json.projects;
    }
    sessionStorage.setItem('catalogueProjects', JSON.stringify(catalogueData));
    renderCatalogue(catalogueData);
  } catch (err) {
    logError('loadCatalogue', err);
    container.innerHTML = '<p>Failed to load project catalogue.</p>';
  }
}

function renderCatalogue(list) {
  const container = document.getElementById('catalogue-projects-list');
  container.innerHTML = list.length
    ? ''
    : '<p class="empty-state">No projects found in this category.</p>';

  catalogueData = list;

  list.forEach(p => {
    const card = document.createElement('article');
    card.className = 'project-card';
    card.setAttribute('role', 'region');
    card.setAttribute('aria-label', `Project: ${p.project_name}`);
    const status = p.status || 'Available';
    const statusIcon = status === 'Completed' ? '✅' : status === 'Locked' ? '🔒' : '';

    card.innerHTML = `
      <h3>${escapeHTML(p.project_name)} ${statusIcon}</h3>
      <p>${escapeHTML(p.description || '')}</p>
      <p>Category: ${escapeHTML(p.category || '')}</p>
    `;

    if (status === 'Locked') card.classList.add('locked');
    if (status === 'Completed') card.classList.add('completed');
    container.appendChild(card);
  });
}

async function startProject(projectKey, btn) {
  if (startingProject) return;
  startingProject = true;
  const buttons = document.querySelectorAll('.build-btn');
  buttons.forEach(b => (b.disabled = true));
  try {
    if (btn) {
      btn.dataset.orig = btn.textContent;
      btn.textContent = 'Starting...';
    }
    const headers = await authHeaders();
    await authJsonFetch('/api/alliance/projects/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken(), ...headers },
      body: JSON.stringify({ project_key: projectKey })
    });

    await loadAllLists();
    setLiveMessage('Project started successfully.');
  } catch (err) {
    logError('startProject', err);
    alert('❌ Failed to start project.');
  } finally {
    startingProject = false;
    buttons.forEach(b => (b.disabled = false));
    if (btn) {
      btn.textContent = btn.dataset.orig || 'Start Project';
      delete btn.dataset.orig;
    }
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
    const data = await authJsonFetch(`/api/alliance/projects/contributions?project_key=${key}`);
    contribList = data.contributions || [];
    contribPage = 0;
    if (contribList.length === 0) {
      listEl.innerHTML = '<p class="empty-state">No contributions.</p>';
    } else {
      renderContribPage();
    }
  } catch (err) {
    logError('openContribModal', err);
    if (listEl) listEl.innerHTML = '<p class="empty-state">Failed to load.</p>';
  }
  openModal(modal);
}

function closeContribModal() {
  contribList = [];
  closeModal('contrib-modal');
}

function renderContribPage() {
  const modal = document.getElementById('contrib-modal');
  const listEl = modal.querySelector('.modal-list');
  const nav = modal.querySelector('.modal-pagination');
  if (!listEl || !Array.isArray(contribList)) return;
  const start = contribPage * CONTRIB_PAGE_SIZE;
  const end = start + CONTRIB_PAGE_SIZE;
  const pageItems = contribList.slice(start, end);
  listEl.innerHTML = pageItems
    .map(r => `<div>${escapeHTML(r.player_name)} - ${r.amount}</div>`)
    .join('');
  const totalPages = Math.ceil(contribList.length / CONTRIB_PAGE_SIZE) || 1;
  if (nav) {
    nav.innerHTML = `
      <button class="btn prev-btn" ${contribPage === 0 ? 'disabled' : ''}>Prev</button>
      <span>${contribPage + 1} / ${totalPages}</span>
      <button class="btn next-btn" ${contribPage >= totalPages - 1 ? 'disabled' : ''}>Next</button>
    `;
    nav.querySelector('.prev-btn')?.addEventListener('click', () => {
      if (contribPage > 0) { contribPage--; renderContribPage(); }
    });
    nav.querySelector('.next-btn')?.addEventListener('click', () => {
      if (contribPage < totalPages - 1) { contribPage++; renderContribPage(); }
    });
  }
}



function formatCostFromColumns(obj) {
  return RESOURCE_KEYS
    .filter(key => typeof obj[key] === 'number' && obj[key] > 0)
    .map(key => `${obj[key]} ${escapeHTML(key.replace(/_cost$/, ''))}`)
    .join(', ') || 'N/A';
}

function totalCost(obj) {
  return RESOURCE_KEYS
    .filter(key => typeof obj[key] === 'number' && obj[key] > 0)
    .reduce((sum, key) => sum + obj[key], 0);
}

function sortProjects(list, sortBy) {
  const key = sortBy || 'name';
  const sorted = [...list];
  if (key === 'category') {
    sorted.sort((a, b) => (a.category || '').localeCompare(b.category || ''));
  } else if (key === 'cost') {
    sorted.sort((a, b) => totalCost(a) - totalCost(b));
  } else {
    sorted.sort((a, b) => (a.project_name || a.name || '').localeCompare(b.project_name || b.name || ''));
  }
  return sorted;
}

function renderSkeletons(container, count = 3) {
  container.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const skel = document.createElement('article');
    skel.className = 'project-card skeleton';
    container.appendChild(skel);
  }
}
