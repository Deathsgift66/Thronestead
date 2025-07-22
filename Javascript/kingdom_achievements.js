// Project Name: Thronestead©
// File Name: kingdom_achievements.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './core_utils.js';

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
