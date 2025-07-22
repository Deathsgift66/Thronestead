// Project Name: Thronestead©
// File Name: research.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML, showToast, formatDate, formatDuration } from './core_utils.js';

let currentSession = null;
let researchChannel = null;
let channelActive = false;
let loading = false;
let loadQueued = false;
const techMap = new Map();

// Utility to escape HTML from strings to prevent XSS



// Toast notifications come from utils

// Countdown updater for active research
function startCountdownTimers() {
  const countdowns = document.querySelectorAll('.countdown');
  countdowns.forEach(el => {
    const endTime = new Date(el.dataset.endsAt).getTime();
    const update = () => {
      const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
      el.textContent = formatDuration(remaining);
      if (remaining <= 0) {
        el.textContent = 'Completed!';
        clearInterval(timer);
      }
    };
    update();
    const timer = setInterval(update, 1000);
  });
}

// Page initializer
export async function initResearchPage() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return location.href = 'login.html';
  currentSession = session;
  await loadResearchData();

  window.addEventListener('beforeunload', async () => {
    if (researchChannel) {
      await supabase.removeChannel(researchChannel);
      channelActive = false;
      researchChannel = null;
    }
  });
}

// Load all research-related UI
async function loadResearchData() {
  if (loading) {
    loadQueued = true;
    return;
  }
  loading = true;

  const tree = document.getElementById('tech-tree');
  const filters = document.getElementById('tech-filters');
  const details = document.getElementById('tech-details');
  const activeEl = document.getElementById('active-research');
  const completedEl = document.getElementById('completed-research');
  const encyclopediaEl = document.getElementById('encyclopedia');

  [tree, filters, details, activeEl, completedEl, encyclopediaEl].forEach(el => {
    if (el) el.innerHTML = '<p>Loading...</p>';
  });

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const { data: userRow } = await supabase
      .from('users').select('kingdom_id').eq('user_id', user.id).single();
    const kingdomId = userRow.kingdom_id;

    if (!channelActive) {
      researchChannel = supabase
        .channel(`research-${kingdomId}`)
        .on(
          'postgres_changes',
          { event: '*', schema: 'public', table: 'kingdom_research_tracking', filter: `kingdom_id=eq.${kingdomId}` },
          () => loadResearchData()
        )
        .subscribe();
      channelActive = true;
    }

    const [{ data: techs, error: techErr }, trackingRes] = await Promise.all([
      supabase.from('tech_catalogue')
        .select('*')
        .eq('is_active', true)
        .order('tier', { ascending: true }),

      fetch('/api/kingdom/research/list', {
        headers: {
          'Authorization': `Bearer ${currentSession.access_token}`,
          'X-User-ID': currentSession.user.id
        }
      })
    ]);

    if (techErr) throw techErr;
    if (!trackingRes.ok) {
      const msg = await trackingRes.text();
      throw new Error(msg || 'Research list failed');
    }

    techMap.clear();
    techs.forEach(t => techMap.set(t.tech_code, t));

    const overview = await trackingRes.json();
    const completed = Array.isArray(overview.completed) ? overview.completed : [];
    const activeList = Array.isArray(overview.in_progress) ? overview.in_progress : [];
    const progress = [
      ...completed.map(t => ({ tech_code: t.tech_code, status: 'completed', ends_at: t.ends_at })),
      ...activeList.map(t => ({ tech_code: t.tech_code, status: 'active', ends_at: t.ends_at }))
    ];
    const active = activeList[0];
    const completedSet = new Set(completed.map(t => t.tech_code));

    renderFilters(techs);
    renderTree(techs, progress, completedSet);
    renderDetails(null, false, false, false, completedSet);
    renderActive(active, techs);
    renderCompleted(completed, techs);
    renderEncyclopedia(completed, techs);
    startCountdownTimers();

  } catch (err) {
    console.error("❌ Failed to load research:", err);
    showToast("Failed to load research tree.");
  } finally {
    loading = false;
    if (loadQueued) {
      loadQueued = false;
      loadResearchData();
    }
  }
}

// Render category filter buttons
function renderFilters(techs) {
  const filters = document.getElementById('tech-filters');
  if (!filters) return;

  filters.innerHTML = '';
  const categories = Array.from(new Set(techs.map(t => t.category))).sort();
  [...categories, 'ALL'].forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'action-btn';
    btn.textContent = cat;
    btn.onclick = () => {
      filterByCategory(cat);
      document.querySelectorAll('#tech-filters .action-btn')
        .forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
    };
    filters.appendChild(btn);
  });
}

// Render the tech nodes into the tree
function renderTree(techs, tracking, completedSet) {
  const tree = document.getElementById('tech-tree');
  if (!tree) return;

  tree.innerHTML = '';
  const completedCodes = tracking.filter(t => t.status === 'completed').map(t => t.tech_code);
  const activeCodes = tracking.filter(t => t.status === 'active').map(t => t.tech_code);

  techs.forEach(tech => {
    const node = document.createElement('div');
    node.className = 'tech-node';
    node.dataset.code = tech.tech_code;
    node.dataset.category = tech.category;

    const isCompleted = completedCodes.includes(tech.tech_code);
    const isActive = activeCodes.includes(tech.tech_code);
    const unlocked = (tech.prerequisites || []).every(p => completedCodes.includes(p));

    if (isCompleted) node.classList.add('completed');
    else if (isActive) node.classList.add('active');
    else if (!unlocked) node.classList.add('locked');

    node.innerHTML = `
      <h4>${escapeHTML(tech.name)}</h4>
      <p>Tier ${tech.tier}</p>
      <p>${escapeHTML(tech.category)}</p>
    `;
    node.onclick = () => renderDetails(tech, isCompleted, isActive, unlocked, completedSet);
    node.tabIndex = 0;
    node.setAttribute('role', 'button');
    node.setAttribute('aria-label', tech.name);
    node.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        node.click();
      }
    });
    tree.appendChild(node);
  });
}

// Filter nodes by category
function filterByCategory(category) {
  document.querySelectorAll('.tech-node').forEach(el => {
    const match = category === 'ALL' || el.dataset.category === category;
    el.style.display = match ? 'block' : 'none';
  });
}

// Show tech details and allow research activation
function renderDetails(tech = null, isCompleted = false, isActive = false, unlocked = false, completedSet = new Set()) {
  const details = document.getElementById('tech-details');
  if (!details) return;

  if (!tech) {
    details.innerHTML = '<p>Select a technology to see details.</p>';
    return;
  }

  const prereqs = Array.isArray(tech.prerequisites) ? tech.prerequisites : [];
  const prereqList = prereqs
    .map(p => {
      const name = techMap.get(p)?.name || p;
      const cls = completedSet.has(p) ? 'prereq done' : 'prereq';
      return `<span class="${cls}">${escapeHTML(name)}</span>`;
    })
    .join(', ') || 'None';

  details.innerHTML = `
    <h3>${escapeHTML(tech.name)}</h3>
    <p>${escapeHTML(tech.description)}</p>
    <p><strong>Category:</strong> ${escapeHTML(tech.category)}</p>
    <p><strong>Tier:</strong> ${tech.tier}</p>
    <p><strong>Prerequisites:</strong> ${prereqList}</p>
    <p><strong>Duration:</strong> ${tech.duration_hours}h</p>
    <p><strong>Status:</strong> ${isCompleted ? 'Completed' : isActive ? 'In Progress' : unlocked ? 'Unlocked' : 'Locked'}</p>
    ${(!isCompleted && !isActive && unlocked)
      ? `<button id="start-research" class="action-btn">Start Research</button>`
      : ''}
  `;

  if (unlocked && !isCompleted && !isActive) {
    document.getElementById('start-research').onclick = async () => {
      const btn = document.getElementById('start-research');
      btn.disabled = true;
      btn.textContent = 'Starting...';
      try {
        const res = await fetch('/api/kingdom/start_research', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${currentSession.access_token}`,
            'X-User-ID': currentSession.user.id
          },
          body: JSON.stringify({ tech_code: tech.tech_code })
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.error || 'Failed');
        showToast('Research started!');
        await loadResearchData();
      } catch (err) {
        console.error(err);
        showToast('Could not start research.');
        btn.disabled = false;
        btn.textContent = 'Start Research';
      }
    };
  }
}

// Display currently active research
function renderActive(active, techs) {
  const el = document.getElementById('active-research');
  if (!el) return;
  el.innerHTML = '';

  if (!active) {
    el.innerHTML = '<p>No active research.</p>';
    return;
  }

  const def = techs.find(t => t.tech_code === active.tech_code);
  const remaining = Math.max(0, Math.floor((new Date(active.ends_at) - Date.now()) / 1000));

  el.innerHTML = `
    <div class="tech-card">
      <h3>${escapeHTML(def?.name || active.tech_code)}</h3>
      <p>${escapeHTML(def?.description || '')}</p>
      <p>Time Remaining: <span class="countdown" data-ends-at="${active.ends_at}">${formatDuration(remaining)}</span></p>
    </div>
  `;
}

// Render list of completed technologies
function renderCompleted(completed, techs) {
  const el = document.getElementById('completed-research');
  if (!el) return;
  el.innerHTML = '';

  if (completed.length === 0) {
    el.innerHTML = '<p>No completed research yet.</p>';
    return;
  }

  completed.forEach(entry => {
    const def = techs.find(t => t.tech_code === entry.tech_code);
    el.innerHTML += `
      <div class="tech-card">
        <h3>${escapeHTML(def?.name || entry.tech_code)}</h3>
        <p>${escapeHTML(def?.description || '')}</p>
        <p>Completed: ${formatDate(entry.ends_at)}</p>
      </div>
    `;
  });
}

// Display lore/encyclopedia for completed techs
function renderEncyclopedia(completed, techs) {
  const el = document.getElementById('encyclopedia');
  if (!el) return;
  el.innerHTML = '';

  if (completed.length === 0) {
    el.innerHTML = '<p>No entries unlocked.</p>';
    return;
  }

  completed.forEach(entry => {
    const def = techs.find(t => t.tech_code === entry.tech_code);
    el.innerHTML += `
      <div class="tech-card">
        <h3>${escapeHTML(def?.name || entry.tech_code)}</h3>
        <p>${escapeHTML(def?.encyclopedia_entry || 'No lore available.')}</p>
      </div>
    `;
  });
}
