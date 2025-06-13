/*
Project Name: Kingmakers Rise Frontend
File Name: achievement.js
Updated: 2025-06-13
Description: Full badge grid w/ search, filters, sorting, live sync, and modal preview
*/

import { supabase } from './supabaseClient.js';

let allAchievements = [];
let filteredAchievements = [];
let currentUser = null;

document.addEventListener('DOMContentLoaded', async () => {
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
    img.src = ach.icon_url || 'Assets/icon-sword.svg';
    img.alt = ach.name;
    card.appendChild(img);

    const name = document.createElement('div');
    name.classList.add('badge-name');
    name.textContent = !ach.is_hidden || ach.is_unlocked ? ach.name : '??? Unknown Deed';
    card.appendChild(name);

    card.addEventListener('click', () => displayAchievementDetail(ach));
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

  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'action-btn';
    btn.textContent = cat;
    btn.addEventListener('click', () => filterByCategory(cat === 'All' ? null : cat));
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
    ? Object.entries(ach.reward).map(([k, v]) => `${k}: ${v}`).join(', ')
    : 'None';

  modal.innerHTML = `
    <h2>${!ach.is_hidden || ach.is_unlocked ? escapeHTML(ach.name) : '???'}</h2>
    <p>${!ach.is_hidden || ach.is_unlocked ? escapeHTML(ach.description) : 'Unlock to reveal details.'}</p>
    <p>Category: ${escapeHTML(ach.category || 'N/A')}</p>
    <p>Reward: ${escapeHTML(reward)}</p>
    <p>Status: ${ach.is_unlocked ? 'Unlocked' : 'Locked'}</p>
    ${ach.awarded_at ? `<p>Earned on: ${new Date(ach.awarded_at).toLocaleString()}</p>` : ''}
    <button class="action-btn" id="close-achievement-modal">Close</button>
  `;
  modal.classList.remove('hidden');
  document.getElementById('close-achievement-modal').addEventListener('click', () => {
    modal.classList.add('hidden');
  });
}

// ✅ Summary bar at top
function updateProgressSummary(list) {
  const summary = document.getElementById('progress-summary');
  if (!summary) return;
  const total = list.length;
  const unlocked = list.filter(a => a.is_unlocked).length;
  const percent = total ? Math.round((unlocked / total) * 100) : 0;
  summary.className = 'progress-summary';
  summary.innerHTML = `
    <p>${unlocked} / ${total} unlocked (${percent}%)</p>
    <div class="progress-bar">
      <div class="progress-fill" style="width:${percent}%"></div>
    </div>
  `;
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
      const { achievements } = await loadKingdomAchievements(currentUser.id);
      filteredAchievements = [...achievements];
      renderAchievementsList(filteredAchievements);
      updateProgressSummary(filteredAchievements);
    })
    .subscribe();
}

// ✅ Safe text
function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
