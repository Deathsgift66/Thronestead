// Project Name: Thronestead©
// File Name: kingdom.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66
// Consolidated kingdom-related scripts. This file combines the former
// edit_kingdom.js, kingdom_achievements.js, kingdom_history.js,
// kingdom_name_linkify.js and projects_kingdom.js modules.

\n// ===== edit_kingdom.js =====
// Project Name: Thronestead©
// File Name: edit_kingdom.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from './supabaseClient.js';
import { showToast } from './utils.js';
import { authHeaders } from './auth.js';
import { setupPreview } from './account_previews.js';

document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('kingdom-form');
  const bannerPreview = document.getElementById('banner-preview');
  const emblemPreview = document.getElementById('emblem-preview');

  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  await loadRegions();

  const res = await fetch('/api/kingdom/profile', {
    headers: await authHeaders()
  });
  const kingdom = await res.json();
  populateForm(kingdom);

  setupPreview('banner_url', 'banner-preview', 'Assets/profile_background.png');
  setupPreview('emblem_url', 'emblem-preview', 'Assets/icon-scroll.svg');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (!validateName()) return;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
      const save = await fetch('/api/kingdom/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(await authHeaders())
        },
        body: JSON.stringify(payload)
      });

      const result = await save.json();
      if (!save.ok) throw new Error(result.detail || 'Update failed');

      showToast('✅ Kingdom updated');
    } catch (err) {
      console.error(err);
      showToast('❌ Failed to update kingdom');
    }
  });
});

function validateName() {
  const el = document.getElementById('kingdom_name');
  const name = el.value.trim();
  const valid = /^[A-Za-z0-9 '\-,]{3,32}$/.test(name);
  if (!valid) {
    showToast('❌ Kingdom Name must be 3–32 letters/numbers');
    el.focus();
  }
  return valid;
}

async function loadRegions() {
  const select = document.getElementById('region');
  if (!select) return;
  try {
    const res = await fetch('/api/kingdom/regions');
    const regions = await res.json();
    select.innerHTML = '<option value="">Select Region</option>';
    regions.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.region_code || r.region_name;
      opt.textContent = r.region_name;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error('Failed to load regions:', err);
    select.innerHTML = '<option value="">Failed to load regions</option>';
  }
}

function populateForm(data) {
  for (const key in data) {
    const el = document.getElementById(key);
    if (el && typeof data[key] === 'string') el.value = data[key];
  }

  const region = document.getElementById('region');
  if (region && data.region) {
    const option = new Option(data.region, data.region, true, true);
    region.appendChild(option);
  }

  if (data.vacation_mode) {
    document.getElementById('vacation-warning')?.classList.remove('hidden');
    const form = document.getElementById('kingdom-form');
    form.classList.add('disabled');
    form.querySelectorAll('input, textarea, select, button').forEach(el => {
      el.disabled = true;
    });
  }
}

\n// ===== kingdom_achievements.js =====
// Project Name: Thronestead©
// File Name: kingdom_achievements.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';

let allAchievements = [];
let filteredAchievements = [];
let currentUser = null;

document.addEventListener('DOMContentLoaded', async () => {
  const grid = document.getElementById('achievement-grid');
  grid?.classList.add('loading');
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return window.location.href = 'login.html';
  currentUser = user;

  const { kingdomId } = await loadKingdomAchievements(user.id);

  filteredAchievements = [...allAchievements];
  renderAchievementsList(filteredAchievements);
  addCategoryFilter(allAchievements);
  setupSearchBar();
  setupSorting();
  updateProgressSummary(filteredAchievements);
  if (kingdomId) subscribeToUpdates(kingdomId);
  grid?.classList.remove('loading');
});

// ✅ Load both unlocked and catalogued achievements
async function loadKingdomAchievements(userId) {
  const { data: kingdom, error } = await supabase
    .from('kingdoms')
    .select('kingdom_id')
    .eq('user_id', userId)
    .single();

  if (error) {
    console.error('Failed to load kingdom ID:', error);
    return { achievements: [], kingdomId: null };
  }

  const [unlocked, all] = await Promise.all([
    supabase.from('kingdom_achievements').select('achievement_code, awarded_at').eq('kingdom_id', kingdom.kingdom_id),
    supabase.from('kingdom_achievement_catalogue').select('*')
  ]);

  if (unlocked.error || all.error) {
    console.error('Error fetching achievements:', unlocked.error || all.error);
    return { achievements: [], kingdomId: kingdom.kingdom_id };
  }

  const unlockedSet = new Set(unlocked.data.map(a => a.achievement_code));

  allAchievements = all.data.map(ach => ({
    ...ach,
    is_unlocked: unlockedSet.has(ach.achievement_code),
    awarded_at: unlocked.data.find(u => u.achievement_code === ach.achievement_code)?.awarded_at || null
  }));

  return { achievements: allAchievements, kingdomId: kingdom.kingdom_id };
}

// ✅ Render badge grid
function renderAchievementsList(list) {
  const grid = document.getElementById('achievement-grid');
  if (!grid) return;
  grid.innerHTML = '';

  if (!list.length) {
    grid.innerHTML = '<p>No achievements found.</p>';
    return;
  }

  list.forEach(ach => {
    const card = document.createElement('div');
    card.className = `achievement-card ${ach.is_unlocked ? 'badge-earned' : 'badge-locked'} ${ach.is_hidden && !ach.is_unlocked ? 'badge-hidden' : ''}`;
    card.dataset.category = ach.category || '';
    card.dataset.name = ach.name.toLowerCase();
    card.dataset.description = (ach.description || '').toLowerCase();

    const img = document.createElement('img');
    img.src = ach.icon_url || '/Assets/icon-sword.svg';
    img.alt = ach.name;
    card.appendChild(img);

    const name = document.createElement('div');
    name.classList.add('badge-name');
    name.textContent = !ach.is_hidden || ach.is_unlocked ? ach.name : '??? Unknown Deed';
    card.appendChild(name);

    let tooltipText = '';
    if (ach.is_hidden && !ach.is_unlocked) {
      tooltipText = 'Unlock to reveal this achievement.';
    } else if (ach.is_unlocked && ach.awarded_at) {
      tooltipText = `Unlocked on ${new Date(ach.awarded_at).toLocaleString()}`;
    }
    if (tooltipText) {
      card.classList.add('tooltip-container');
      const tip = document.createElement('span');
      tip.className = 'tooltip-text';
      tip.textContent = tooltipText;
      card.appendChild(tip);
    }

    card.tabIndex = 0;
    card.addEventListener('click', () => displayAchievementDetail(ach));
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        displayAchievementDetail(ach);
      }
    });

    grid.appendChild(card);
  });
}

// ✅ Toolbar with filters + category buttons
function addCategoryFilter(achievements) {
  const toolbar = document.getElementById('filter-toolbar');
  if (!toolbar) return;

  toolbar.innerHTML = '';

  const search = document.createElement('input');
  search.type = 'text';
  search.placeholder = 'Search achievements...';
  search.id = 'achievement-search';
  toolbar.appendChild(search);

  const sortSelect = document.createElement('select');
  sortSelect.id = 'achievement-sort';
  sortSelect.innerHTML = `
    <option value="name">Name</option>
    <option value="category">Category</option>
    <option value="points">Points</option>
    <option value="status">Unlocked</option>
  `;
  toolbar.appendChild(sortSelect);

  const categories = [...new Set(achievements.map(a => a.category).filter(Boolean))].sort();
  categories.unshift('All');

  categories.forEach((cat, idx) => {
    const btn = document.createElement('button');
    btn.className = 'action-btn';
    btn.dataset.filter = cat.toLowerCase();
    btn.textContent = cat;
    if (idx === 0) btn.classList.add('active');
    btn.addEventListener('click', () => {
      document.querySelector('.filter-toolbar .active')?.classList.remove('active');
      btn.classList.add('active');
      filterByCategory(cat === 'All' ? null : cat);
    });
    toolbar.appendChild(btn);
  });
}

// ✅ Category filtering logic
function filterByCategory(category) {
  filteredAchievements = category
    ? allAchievements.filter(a => a.category === category)
    : [...allAchievements];
  applySearch(document.getElementById('achievement-search')?.value || '');
}

// ✅ Live search
function setupSearchBar() {
  const input = document.getElementById('achievement-search');
  if (!input) return;
  input.addEventListener('input', e => applySearch(e.target.value));
}

// ✅ Search + sorting combo logic
function applySearch(keyword) {
  keyword = keyword.toLowerCase();
  let list = filteredAchievements.filter(a =>
    a.name.toLowerCase().includes(keyword) || (a.description || '').toLowerCase().includes(keyword)
  );
  const sortMethod = document.getElementById('achievement-sort')?.value || 'name';
  list = sortAchievements(list, sortMethod);
  renderAchievementsList(list);
  updateProgressSummary(list);
}

// ✅ Sorting selector setup
function setupSorting() {
  const select = document.getElementById('achievement-sort');
  if (!select) return;
  select.addEventListener('change', () =>
    applySearch(document.getElementById('achievement-search')?.value || '')
  );
}

// ✅ Actual sort logic
function sortAchievements(list, method) {
  const arr = [...list];
  switch (method) {
    case 'category': return arr.sort((a, b) => (a.category || '').localeCompare(b.category || ''));
    case 'points': return arr.sort((a, b) => (b.points || 0) - (a.points || 0));
    case 'status': return arr.sort((a, b) => Number(b.is_unlocked) - Number(a.is_unlocked));
    default: return arr.sort((a, b) => a.name.localeCompare(b.name));
  }
}

// ✅ Modal popup with full details
function displayAchievementDetail(ach) {
  const modal = document.getElementById('achievement-modal');
  if (!modal) return;

  const reward = ach.reward && Object.keys(ach.reward).length
    ? Object.entries(ach.reward).map(([k, v]) => `${escapeHTML(k)}: ${escapeHTML(v)}`).join(', ')
    : 'None';

  modal.innerHTML = `
    <div class="modal-content">
      <button class="modal-close" aria-label="Close details" onclick="closeModal()">×</button>
      <h3 id="achievement-modal-title">${!ach.is_hidden || ach.is_unlocked ? escapeHTML(ach.name) : '???'}</h3>
      <p>${!ach.is_hidden || ach.is_unlocked ? escapeHTML(ach.description) : 'Unlock to reveal details.'}</p>
      <img src="${ach.icon_url || '/Assets/icon-sword.svg'}" alt="${escapeHTML(ach.name)}" />
      <p><strong>Points:</strong> ${ach.points || 0}</p>
      <p><strong>Category:</strong> ${escapeHTML(ach.category || 'N/A')}</p>
      <p><strong>Reward:</strong> ${reward}</p>
    </div>`;
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
}

function closeModal() {
  const modal = document.getElementById('achievement-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

// ✅ Summary bar at top
function updateProgressSummary(list) {
  const summary = document.getElementById('progress-summary');
  if (!summary) return;
  const total = list.length;
  const unlocked = list.filter(a => a.is_unlocked).length;
  const percent = total ? Math.round((unlocked / total) * 100) : 0;

  document.getElementById('achieved-count').textContent = unlocked;
  document.getElementById('total-count').textContent = total;
  const progress = document.getElementById('achievement-progress');
  if (progress) progress.value = percent;
}

// ✅ Live updates from Supabase channel
function subscribeToUpdates(kingdomId) {
  supabase
    .channel(`kingdom_achievements_${kingdomId}`)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'kingdom_achievements',
      filter: `kingdom_id=eq.${kingdomId}`
    }, async () => {
      const grid = document.getElementById('achievement-grid');
      grid?.classList.add('loading');
      const { achievements } = await loadKingdomAchievements(currentUser.id);
      filteredAchievements = [...achievements];
      renderAchievementsList(filteredAchievements);
      updateProgressSummary(filteredAchievements);
      grid?.classList.remove('loading');
    })
    .subscribe();
}

// ✅ Safe text
\n// ===== kingdom_history.js =====
// Project Name: Thronestead©
// File Name: kingdom_history.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML, formatDate } from './utils.js';

let kingdomId = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return (window.location.href = 'login.html');

  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;

  const authHeaders = {
    'Authorization': `Bearer ${session.access_token}`,
    'X-User-ID': user.id
  };

  const { data: userData, error } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', user.id)
    .single();

  if (error || !userData?.kingdom_id) return;

  kingdomId = userData.kingdom_id;
  await loadFullHistory(authHeaders);
  bindCollapsibles();
  subscribeToRealtime();
});

async function loadFullHistory(headers) {
  try {
    const res = await fetch(`/api/kingdom-history/${kingdomId}/full`, { headers });
    const data = await res.json();

    renderTimeline(data.timeline || []);
    renderAchievements(data.achievements || []);
    renderLog('war-log', data.wars_fought || [], e => `War ID ${e.war_id}`);
    renderLog('project-log', data.projects_log || [], e => escapeHTML(e.name));
    renderLog('quest-log', data.quests_log || [], e => `${e.quest_code} - ${e.status}`);
    renderLog('training-log', data.training_log || [], e => `${e.quantity} × ${e.unit_name}`);
  } catch (err) {
    console.error('Failed to load history:', err);
  }
}

function renderTimeline(events) {
  const timeline = document.getElementById('timeline');
  timeline.innerHTML = '';
  if (!events.length) {
    timeline.innerHTML = '<li>No events found.</li>';
    return;
  }
  events.forEach(event => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${formatDate(event.event_date)}</strong>: ${escapeHTML(event.event_details)}`;
    timeline.appendChild(li);
  });
}

function renderAchievements(list) {
  const grid = document.getElementById('achievement-grid');
  if (!grid) return;
  grid.innerHTML = '';
  list.forEach(a => {
    const badge = document.createElement('div');
    badge.classList.add('achievement-badge');
    badge.textContent = escapeHTML(a.name);
    grid.appendChild(badge);
  });
}

function renderLog(containerId, entries, formatter) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  if (!entries.length) {
    container.innerHTML = '<li>No entries found.</li>';
    return;
  }
  entries.forEach(entry => {
    const li = document.createElement('li');
    li.innerHTML = formatter(entry);
    container.appendChild(li);
  });
}

function bindCollapsibles() {
  document.querySelectorAll('.collapsible h3').forEach(header => {
    header.addEventListener('click', () => {
      header.parentElement.classList.toggle('open');
      const chevron = header.querySelector('.chevron');
      chevron.textContent = header.parentElement.classList.contains('open') ? '▼' : '▶';
    });
  });
}

function subscribeToRealtime() {
  supabase.channel('history-' + kingdomId)
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'kingdom_history_log',
      filter: `kingdom_id=eq.${kingdomId}`
    }, payload => addTimelineEntry(payload.new))
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'kingdom_achievements',
      filter: `kingdom_id=eq.${kingdomId}`
    }, payload => addAchievementBadge(payload.new))
    .subscribe();
}

function addTimelineEntry(entry) {
  const li = document.createElement('li');
  li.innerHTML = `<strong>${formatDate(entry.event_date)}</strong>: ${escapeHTML(entry.event_details)}`;
  document.getElementById('timeline').prepend(li);
}

function addAchievementBadge(rec) {
  const badge = document.createElement('div');
  badge.classList.add('achievement-badge');
  badge.textContent = escapeHTML(rec.name || rec.achievement_code);
  document.getElementById('achievement-grid').prepend(badge);
}



\n// ===== kingdom_name_linkify.js =====
// Project Name: Thronestead©
// File Name: kingdom_name_linkify.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Utility to linkify kingdom names in text content.
'use strict';

let kingdomMap = null;

async function loadKingdomMap() {
  if (kingdomMap) return kingdomMap;
  const cached = sessionStorage.getItem('kingdomMap');
  if (cached) {
    kingdomMap = JSON.parse(cached);
    return kingdomMap;
  }
  try {
    const res = await fetch('/api/kingdom/lookup');
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    kingdomMap = {};
    for (const row of data) {
      const id = row.kingdom_id ?? row.id;
      const name = row.kingdom_name ?? row.name;
      kingdomMap[name.toLowerCase()] = id;
    }
    sessionStorage.setItem('kingdomMap', JSON.stringify(kingdomMap));
  } catch (err) {
    console.error('Failed to load kingdom lookup', err);
    kingdomMap = {};
  }
  return kingdomMap;
}

function linkifyKingdoms(text) {
  if (!kingdomMap) return text;
  const pattern = /\b([A-Z][A-Za-z'\-]*(?:\s+[A-Z][A-Za-z'\-]*)*)\b/g;
  return text.replace(pattern, (m) => {
    const id = kingdomMap[m.toLowerCase()];
    if (id) {
      return `<a href="/kingdom_profile.html?kingdom_id=${id}" target="_blank" rel="noopener noreferrer">${m}</a>`;
    }
    return m;
  });
}

export async function applyKingdomLinks(containerSelector = '.message-content, .log-entry, .notification-body') {
  if (!kingdomMap) await loadKingdomMap();
  document.querySelectorAll(containerSelector).forEach((el) => {
    const original = el.textContent;
    const html = linkifyKingdoms(original);
    if (html !== original) {
      el.innerHTML = html;
    }
  });
}
\n// ===== projects_kingdom.js =====
// Project Name: Thronestead©
// File Name: projects_kingdom.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML, showToast, formatDuration, formatCostFromColumns } from './utils.js';
import { RESOURCE_KEYS } from './resources.js';

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

  // ✅ Bind tab switching with keyboard support
  const tabButtons = Array.from(document.querySelectorAll('.tab-btn'));
  function activateTab(btn) {
    tabButtons.forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tab => {
      tab.classList.add('hidden');
      tab.classList.remove('active');
    });
    btn.classList.add('active');
    const targetId = btn.dataset.tab;
    const target = document.getElementById(targetId);
    target.classList.remove('hidden');
    target.classList.add('active');
    btn.focus();
  }

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => activateTab(btn));
  });

  const tabNav = document.querySelector('.tab-buttons');
  tabNav.addEventListener('keydown', e => {
    const idx = tabButtons.indexOf(document.activeElement);
    if (idx === -1) return;
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const next = tabButtons[(idx + 1) % tabButtons.length];
      activateTab(next);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prev = tabButtons[(idx - 1 + tabButtons.length) % tabButtons.length];
      activateTab(prev);
    }
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
        <p>Build Time: ${formatDuration(project.build_time_seconds || 0)}</p>
        ${project.project_duration_seconds ? `<p>Duration: ${formatDuration(project.project_duration_seconds)}</p>` : ''}
        <p>Power Score: ${project.power_score}</p>
        <button class="action-btn start-project-btn" data-code="${project.project_code}" ${isActive || !canAfford ? "disabled" : ""}
          aria-label="Start project"
          aria-disabled="${isActive || !canAfford ? 'true' : 'false'}">
          ${isActive ? "Already Active" : canAfford ? "Start Project" : "Insufficient Resources"}
        </button>
      `;

      availableList.appendChild(card);
    });

    // ✅ Bind start project buttons
    const startBtns = availableList.querySelectorAll('.start-project-btn');
    startBtns.forEach(btn => {
      btn.addEventListener('click', async () => {
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

          showToast(result.message || 'Project started!');
          await loadProjects(); // Refresh

        } catch (err) {
          console.error('❌ Error starting project:', err);
          showToast('Failed to start project.', 'error');
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
        <p>Time Remaining: <span class="countdown" data-ends-at="${activeProject.ends_at}">${formatDuration(remainingTime)}</span></p>
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

// ✅ Start countdown timers
function startCountdowns() {
  const countdownEls = document.querySelectorAll('.countdown');

  countdownEls.forEach(el => {
    const endTime = Date.parse(el.dataset.endsAt);
    if (Number.isNaN(endTime)) {
      el.textContent = 'Invalid date';
      return;
    }

    const update = () => {
      const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
      el.textContent = formatDuration(remaining);

      if (remaining <= 0) {
        clearInterval(timerId);
        el.textContent = 'Completed!';
      }
    };

    update();
    const timerId = setInterval(update, 1000);
  });
}

// ✅ Format time


