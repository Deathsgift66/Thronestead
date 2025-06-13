/*
Project Name: Kingmakers Rise Frontend
File Name: research.js
Author: Deathsgift66 (Enhanced by ChatGPT)
Description: Handles research tech tree rendering, activation, real-time updates, and encyclopedia entries.
*/

import { supabase } from './supabaseClient.js';

let currentSession = null;
let researchChannel = null;

// Utility to escape HTML from strings to prevent XSS
function escapeHTML(str) {
  return str ? String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;") : '';
}

// Format seconds into human-readable string
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

// Toast notification handler
function showToast(message) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// Countdown updater for active research
function startCountdownTimers() {
  const countdowns = document.querySelectorAll('.countdown');
  countdowns.forEach(el => {
    const endTime = new Date(el.dataset.endsAt).getTime();
    const update = () => {
      const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
      el.textContent = formatTime(remaining);
      if (remaining > 0) requestAnimationFrame(update);
      else el.textContent = 'Completed!';
    };
    update();
  });
}

// Initialize page once DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return location.href = 'login.html';
  currentSession = session;
  await loadResearchData();
});

window.addEventListener('beforeunload', () => {
  if (researchChannel) supabase.removeChannel(researchChannel);
});

// Load all research-related UI
async function loadResearchData() {
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

    // Subscribe to live research updates
    if (!researchChannel) {
      researchChannel = supabase
        .channel(`research-${kingdomId}`)
        .on('postgres_changes', {
          event: '*',
          schema: 'public',
          table: 'kingdom_research_tracking',
          filter: `kingdom_id=eq.${kingdomId}`
        }, loadResearchData)
        .subscribe();
    }

    const [{ data: techs }, trackingRes] = await Promise.all([
      supabase.from('tech_catalogue')
        .select('*')
        .eq('is_active', true)
        .order('tier', { ascending: true }),

      fetch('/api/kingdom/research', {
        headers: {
          'Authorization': `Bearer ${currentSession.access_token}`,
          'X-User-ID': currentSession.user.id
        }
      })
    ]);

    const tracking = await trackingRes.json();
    const completed = tracking.research.filter(r => r.status === 'completed');
    const active = tracking.research.find(r => r.status === 'active');

    renderFilters(techs);
    renderTree(techs, tracking.research);
    renderDetails(); // default blank
    renderActive(active, techs);
    renderCompleted(completed, techs);
    renderEncyclopedia(completed, techs);
    startCountdownTimers();

  } catch (err) {
    console.error("❌ Failed to load research:", err);
    showToast("Failed to load research tree.");
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
    btn.onclick = () => filterByCategory(cat);
    filters.appendChild(btn);
  });
}

// Render the tech nodes into the tree
function renderTree(techs, tracking) {
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
    node.onclick = () => renderDetails(tech, isCompleted, isActive, unlocked);
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
function renderDetails(tech = null, isCompleted = false, isActive = false, unlocked = false) {
  const details = document.getElementById('tech-details');
  if (!details) return;

  if (!tech) {
    details.innerHTML = '<p>Select a technology to see details.</p>';
    return;
  }

  const prereqs = tech.prerequisites || [];
  const prereqList = prereqs.map(p => `<span class="prereq">${escapeHTML(p)}</span>`).join(', ') || 'None';

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
      <p>Time Remaining: <span class="countdown" data-ends-at="${active.ends_at}">${formatTime(remaining)}</span></p>
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
        <p>Completed: ${new Date(entry.ends_at).toLocaleString()}</p>
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
