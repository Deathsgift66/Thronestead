// Project Name: Thronestead©
// File Name: alliance_quests.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import {
  escapeHTML,
  showToast,
  enforceAllianceOrAdminAccess,
  authFetch,
  toggleLoading,
  safeUUID,
  openModal,
  closeModal,
  debounce
} from './utils.js';
import { initCsrf, getCsrfToken, rotateCsrfToken } from './security/csrf.js';

initCsrf();
setInterval(rotateCsrfToken, 15 * 60 * 1000);

const t = window.t || (s => s);

let modalEl;
const loadQuestsDebounced = debounce(loadQuests, 300);
const searchDebounced = debounce(() => {
  currentPage = 1;
  debouncedRender();
}, 250);
let inAction = false;
let lastFocusedEl = null;
const csrfPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const isValidCsrf = token => csrfPattern.test(token);
const focusableSelectors = 'button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])';

const safeStorage = (key, validator, fallback = "") => {
  const val = sessionStorage.getItem(key);
  if (validator(val)) return val;
  sessionStorage.removeItem(key);
  return fallback;
};
let allQuests = [];
let currentPage = 1;
let pageSize = 10;
let searchValue = safeStorage("questSearch", v => typeof v === "string" && v.length <= 100, "");
let currentCategory = safeStorage("questCategory", v => typeof v === "string" && v.length <= 50, "");


/**
 * Fetch and render quests for the selected status tab.
 * @param {string} status active|completed|expired
 */
export async function loadQuests(status = 'active') {
  toggleLoading(true);
  const board = document.getElementById('quest-board');
  board?.setAttribute('aria-busy', 'true');
  try {
  const res = await authFetch(`/api/alliance/quests?status=${status}`);
  if (!res.ok) throw new Error(await res.text());
  allQuests = res.ok ? await res.json() : [];
  const sel = document.getElementById('quest-category-filter');
  if (sel) {
  const cats = [...new Set(allQuests.map(q => q.category).filter(Boolean))].sort();
  sel.innerHTML = `<option value="">${t('All Types')}</option>` +
  cats.map(c => `<option value="${escapeHTML(c)}">${escapeHTML(c)}</option>`).join('');
  if (currentCategory && sel.querySelector(`option[value="${CSS.escape(currentCategory)}"]`)) {
  sel.value = currentCategory;
  } else {
  currentCategory = '';
  sessionStorage.setItem('questCategory', currentCategory);
  }
  }
  const searchInput = document.getElementById('quest-search');
  if (searchInput) searchInput.value = searchValue;
  currentPage = 1;
  renderQuestPage();
  } catch (err) {
  console.error('Quest fetch error:', err);
  document.getElementById('quest-board').textContent = t('Failed to load quests.');
  showToast(t('Failed to load quests'), 'error');
  } finally {
  toggleLoading(false);
  board?.setAttribute('aria-busy', 'false');
  }
}

function renderQuestPage() {
  const board = document.getElementById('quest-board');
  const msg = document.getElementById('no-quests-message');
  const searchInput = document.getElementById('quest-search');
  const search = searchInput?.value.trim().toLowerCase() || '';
  searchValue = searchInput?.value || '';
  const filtered = allQuests.filter(q => {
  const name = (q.name || '').toLowerCase();
  const desc = (q.description || '').toLowerCase();
  const matchesSearch = name.includes(search) || desc.includes(search);
  const matchesCat = !currentCategory || q.category === currentCategory;
  return matchesSearch && matchesCat;
  });
  const start = (currentPage - 1) * pageSize;
  const pageQuests = filtered.slice(start, start + pageSize);
  board.innerHTML = '';
  if (!pageQuests.length) {
  msg.classList.remove('hidden');
  } else {
  msg.classList.add('hidden');
  const frag = document.createDocumentFragment();
  pageQuests.forEach(q => frag.appendChild(renderQuestCard(q)));
  board.appendChild(frag);
  }
  document.querySelectorAll('.page-info').forEach(el => {
  el.textContent = `Page ${currentPage} of ${Math.max(1, Math.ceil(filtered.length / pageSize))}`;
  });
  document.querySelectorAll('.prev-page').forEach(btn => {
  btn.disabled = currentPage === 1;
  });
  document.querySelectorAll('.next-page').forEach(btn => {
  btn.disabled = start + pageSize >= filtered.length;
  });
  initCountdowns();
}

const debouncedRender = debounce(renderQuestPage, 200);

// Open quest modal when a card button is clicked
function bindUI() {
  const searchEl = document.getElementById('quest-search');
  if (searchEl) searchEl.value = searchValue;
  // Bind tab clicks
  document.querySelectorAll('.filter-tab').forEach(btn => {
  btn.addEventListener('click', () => {
  document.querySelectorAll('.filter-tab').forEach(b => {
  b.classList.remove('active');
  b.setAttribute('aria-pressed', 'false');
  });
  btn.classList.add('active');
  btn.setAttribute('aria-pressed', 'true');
  sessionStorage.setItem('lastTab', btn.dataset.filter);
  loadQuestsDebounced(btn.dataset.filter);
  });
  });

  document.getElementById('quest-search')?.addEventListener('input', e => {
  searchValue = e.target.value;
  sessionStorage.setItem('questSearch', searchValue);
  searchDebounced();
  });

  document.querySelectorAll('.prev-page').forEach(btn =>
  btn.addEventListener('click', () => {
  if (currentPage > 1) {
  currentPage--;
  renderQuestPage();
  }
  })
  );
  document.querySelectorAll('.next-page').forEach(btn =>
  btn.addEventListener('click', () => {
  currentPage++;
  renderQuestPage();
  })
  );
  document.getElementById('page-size')?.addEventListener('change', e => {
  pageSize = +e.target.value;
  currentPage = 1;
  debouncedRender();
  });
  document.getElementById('quest-category-filter')?.addEventListener('change', e => {
  currentCategory = e.target.value;
  sessionStorage.setItem('questCategory', currentCategory);
  currentPage = 1;
  debouncedRender();
  });

  const boardEl = document.getElementById('quest-board');
  boardEl.addEventListener('click', e => {
  const card = e.target.closest('.view-quest-btn');
  if (!card || !card.dataset.id) return;
  openQuestModal(card.dataset.id);
  });

  modalEl = document.getElementById('quest-modal');
  modalEl.querySelector('[data-testid="modal-close"]').addEventListener('click', closeQuestModal);

  document.getElementById('start-new-quest')?.addEventListener('click', openStartQuestModal);
  document.querySelector('#quest-start-modal [data-testid="modal-close"]')?.addEventListener('click', () => closeModal('quest-start-modal'));
  document.getElementById('confirm-start-quest')?.addEventListener('click', startSelectedQuest);
}

/**
 * Render a quest preview card.
 */
function getQuestCardHTML(q) {
  const progress =
  q.status === 'active' && typeof q.progress === 'number' && !isNaN(q.progress)
  ? Number(q.progress)
  : null;
  const progressHtml = progress !== null
  ? `<div class="quest-progress-bar"><div class="quest-progress-bar-inner" style="width: ${progress}%"></div></div><p class="progress-label">${progress}%</p>`
  : '';
  return `
  <h3 class="quest-title">${escapeHTML(q.name)}</h3>
  <p class="quest-type" data-testid="quest-type">${escapeHTML(q.type || 'Quest')}</p>
  ${progressHtml}
  <p>${escapeHTML(q.description)}</p>
  <p>${t('Ends in:')} <span data-end-time="${q.ends_at || ''}">--:--:--</span></p>
  <button class="view-quest-btn" data-id="${q.id || q.quest_code}" data-testid="view-quest">View</button>`;
}

function renderQuestCard(q) {
  const div = document.createElement('div');
  div.className = 'quest-card';
  div.setAttribute('data-testid', 'quest-card');
  div.innerHTML = getQuestCardHTML(q);
  return div;
}

/**
 * Populate and display the quest modal.
 */
async function openQuestModal(id) {
  inAction = false;
  lastFocusedEl = document.activeElement;
  try {
  toggleLoading(true);
  const res = await authFetch(`/api/alliance/quests/${id}`);
  const q = res.ok ? await res.json() : {};
  document.getElementById('modal-quest-title').textContent = escapeHTML(q.name);
  document.querySelector('.quest-type-modal').textContent = escapeHTML(q.type || 'Quest');
  document.getElementById('modal-quest-description').textContent = escapeHTML(q.description);
  startModalCountdown(q.ends_at);

  const contrib = document.getElementById('modal-quest-contributions');
  contrib.innerHTML = '';
  Object.entries(q.contributions || {})
  .sort(([a], [b]) => a.localeCompare(b))
  .forEach(([k, v]) => {
  const li = document.createElement('li');
  li.setAttribute('data-testid', 'contribution-line');
  li.textContent = `${k.charAt(0).toUpperCase() + k.slice(1)}: ${v.current} / ${v.required}`;
  contrib.appendChild(li);
  });
  if (!contrib.children.length) contrib.innerHTML = '<li>No contributions listed.</li>';

  const rewards = document.getElementById('modal-quest-rewards');
  rewards.innerHTML = '';
  Object.entries(q.rewards || {})
  .sort(([a], [b]) => a.localeCompare(b))
  .forEach(([k, v]) => {
  const li = document.createElement('li');
  li.setAttribute('data-testid', 'reward-line');
  li.textContent = `${k}: ${v}`;
  li.title = `${k} - ${v}`;
  rewards.appendChild(li);
  });
  if (!rewards.children.length) rewards.innerHTML = '<li>No rewards listed.</li>';

  const acceptBtn = document.getElementById('accept-quest-button');
  const claimBtn = document.getElementById('claim-reward-button');
  const contribBtn = document.getElementById('contribute-progress-button');
  acceptBtn.classList.toggle('hidden', q.status !== 'active');
  contribBtn.classList.toggle('hidden', q.status !== 'active');
  claimBtn.classList.toggle('hidden', q.status !== 'completed' || !q.claimable);

  acceptBtn.onclick = async () => {
  if (inAction || !confirm(t('Accept this quest?'))) return;
  if (!isValidCsrf(getCsrfToken())) { showToast(t('Invalid session'), 'error'); return; }
  inAction = true;
  acceptBtn.disabled = true;
  acceptBtn.classList.add('loading');
  toggleLoading(true);
  try {
  const res2 = await authFetch(`/api/alliance/quests/${id}/accept`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() }
  });
  if (res2.ok) {
  showToast(t('Quest accepted!'), 'success');
  closeQuestModal();
  loadQuests('active');
  } else {
  showToast(t('Failed to accept quest'), 'error');
  }
  } catch (err) {
  console.error('Accept quest error:', err);
  showToast(t('Failed to accept quest'), 'error');
  } finally {
  toggleLoading(false);
  acceptBtn.disabled = false;
  acceptBtn.classList.remove('loading');
  inAction = false;
  }
  };
  claimBtn.onclick = async () => {
  if (inAction || !confirm(t('Claim reward for this quest?'))) return;
  if (!isValidCsrf(getCsrfToken())) { showToast(t('Invalid session'), 'error'); return; }
  inAction = true;
  claimBtn.disabled = true;
  claimBtn.classList.add('loading');
  toggleLoading(true);
  try {
  const res2 = await authFetch(`/api/alliance/quests/${id}/claim`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() }
  });
  if (res2.ok) {
  showToast(t('Reward claimed!'), 'success');
  closeQuestModal();
  loadQuests('completed');
  } else {
  showToast(t('Failed to claim reward'), 'error');
  }
  } catch (err) {
  console.error('Claim reward error:', err);
  showToast(t('Failed to claim reward'), 'error');
  } finally {
  toggleLoading(false);
  claimBtn.disabled = false;
  claimBtn.classList.remove('loading');
  inAction = false;
  }
  };
  contribBtn.onclick = async () => {
  if (inAction) return;
  if (!isValidCsrf(getCsrfToken())) { showToast(t('Invalid session'), 'error'); return; }
  inAction = true;
  contribBtn.disabled = true;
  contribBtn.classList.add('loading');
  toggleLoading(true);
  try {
  const res2 = await authFetch('/api/alliance/quests/progress', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() },
  body: JSON.stringify({ quest_code: id, amount: 1 })
  });
  if (res2.ok) {
  showToast(t('Contribution added!'), 'success');
  openQuestModal(id);
  loadQuests('active');
  } else {
  showToast(t('Contribution failed'), 'error');
  }
  } catch (err) {
  console.error('Contribute error:', err);
  showToast(t('Contribution failed'), 'error');
  } finally {
  toggleLoading(false);
  contribBtn.disabled = false;
  contribBtn.classList.remove('loading');
  inAction = false;
  }
  };

  document.getElementById('role-check-message').textContent = escapeHTML(q.role_check_message || '');
  document.getElementById('modal-quest-leader-note').textContent = escapeHTML(q.leader_note || '');

  document.querySelector('main')?.setAttribute('aria-hidden', 'true');
  modalEl.addEventListener('keydown', trapFocus);
  document.addEventListener('keydown', handleEsc);
  modalEl.classList.add('visible');
  modalEl.setAttribute('tabindex', '0');
  modalEl.focus();
  } catch (err) {
  if (err && err.message === 'Unauthorized') return;
  console.error('Quest modal load error:', err);
  showToast(t('Failed to load quest details.'), 'error');
  } finally {
  toggleLoading(false);
  }
}

/** Format ms to human readable duration */
function formatDuration(ms) {
  if (!ms || ms < 0) return '0s';
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  const parts = [];
  if (h) parts.push(`${h}h`);
  if (m) parts.push(`${m}m`);
  if (secs || parts.length === 0) parts.push(`${secs}s`);
  return parts.join(' ');
}

let countdownInterval;
let modalCountdownId;
function initCountdowns() {
  clearInterval(countdownInterval);
  countdownInterval = setInterval(() => {
  document.querySelectorAll('[data-end-time]').forEach(el => {
  const diff = new Date(el.dataset.endTime) - Date.now();
  el.textContent = formatDuration(diff);
  });
  }, 1000);
  // initial render
  document.querySelectorAll('[data-end-time]').forEach(el => {
  const diff = new Date(el.dataset.endTime) - Date.now();
  el.textContent = formatDuration(diff);
  });
}

function startModalCountdown(endTime) {
  clearTimeout(modalCountdownId);
  const el = document.getElementById('modal-time-left');
  const update = () => {
  const diff = new Date(endTime) - Date.now();
  el.textContent = formatDuration(diff);
  if (diff > 0) modalCountdownId = setTimeout(update, 1000);
  };
  update();
}

function closeQuestModal() {
  modalEl.classList.remove('visible');
  modalEl.removeEventListener('keydown', trapFocus);
  document.removeEventListener('keydown', handleEsc);
  document.querySelector('main')?.removeAttribute('aria-hidden');
  clearTimeout(modalCountdownId);
  if (lastFocusedEl) lastFocusedEl.focus();
  modalEl.removeAttribute('tabindex');
}

function trapFocus(e) {
  if (e.key !== 'Tab') return;
  const focusables = Array.from(modalEl.querySelectorAll(focusableSelectors)).filter(el => !el.disabled && el.getAttribute('tabindex') !== '-1');
  if (!focusables.length) return;
  const first = focusables[0];
  const last = focusables[focusables.length - 1];
  if (e.shiftKey) {
  if (document.activeElement === first) {
  last.focus();
  e.preventDefault();
  }
  } else if (document.activeElement === last) {
  first.focus();
  e.preventDefault();
  }
}

function handleEsc(e) {
  if (e.key === 'Escape') closeQuestModal();
}

async function openStartQuestModal() {
  const modal = document.getElementById('quest-start-modal');
  const select = document.getElementById('quest-template-select');
  if (!modal || !select) return;
  select.innerHTML = `<option>${t('Loading...')}</option>`;
  openModal(modal);
  try {
  const res = await authFetch('/api/alliance/quests?status=available');
  const list = res.ok ? await res.json() : [];
  select.innerHTML = list
  .map(q => `<option value="${q.quest_code}">${escapeHTML(q.name)}</option>`)
  .join('') || `<option>${t('No quests available')}</option>`;
  } catch (err) {
  select.innerHTML = `<option>${t('Error loading')}</option>`;
  console.error('Quest load failed', err);
  }
}

async function startSelectedQuest() {
  const select = document.getElementById('quest-template-select');
  const code = select?.value;
  if (!code) return;
  if (!isValidCsrf(getCsrfToken())) { showToast(t('Invalid session'), 'error'); return; }
  const btn = document.getElementById('confirm-start-quest');
  btn.disabled = true;
  btn.classList.add('loading');
  toggleLoading(true);
  try {
  const res = await authFetch('/api/alliance/quests/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() },
  body: JSON.stringify({ quest_code: code })
  });
  if (res.ok) {
  showToast(t('Quest started!'), 'success');
  closeModal('quest-start-modal');
  loadQuests('active');
  } else {
  showToast(t('Failed to start quest'), 'error');
  }
  } catch (err) {
  console.error('Start quest error:', err);
  showToast(t('Failed to start quest'), 'error');
  } finally {
  toggleLoading(false);
  btn.disabled = false;
  btn.classList.remove('loading');
  }
}

async function loadHeroes() {
  const ul = document.getElementById('hero-list');
  ul.innerHTML = '';
  for (let i = 0; i < 3; i++) {
  const li = document.createElement('li');
  li.className = 'loading-skeleton';
  ul.appendChild(li);
  }
  const cacheKey = 'heroesCache';
  const cached = JSON.parse(sessionStorage.getItem(cacheKey) || 'null');
  if (cached && Date.now() - cached.ts < 300000) {
  renderHeroes(cached.data);
  return;
  }
  try {
  const res = await authFetch('/api/alliance/quests/heroes');
  const heroes = res.ok ? await res.json() : [];
  sessionStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), data: heroes }));
  renderHeroes(heroes);
  } catch (err) {
  ul.innerHTML = `<li>${t('Failed to load heroes.')}</li>`;
  console.error(err);
  showToast(t('Failed to load heroes'), 'error');
  }
}

function renderHeroes(list) {
  const ul = document.getElementById('hero-list');
  ul.innerHTML = '';
  list.forEach(h => {
  const li = document.createElement('li');
  li.textContent = `${h.name}: ${h.quests_completed} quests`;
  ul.appendChild(li);
  });
  if (!list.length) {
  ul.innerHTML = `<li>${t('No heroes found.')}</li>`;
  }
}

function initThemeToggle() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const saved = localStorage.getItem('theme') || document.body.getAttribute('data-theme');
  document.body.setAttribute('data-theme', saved);
  btn.textContent = saved === 'dark' ? 'Light Mode' : 'Dark Mode';
  btn.setAttribute('aria-pressed', saved === 'dark');
  btn.setAttribute('aria-label', saved === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  btn.addEventListener('click', () => {
  const current = document.body.getAttribute('data-theme') === 'dark' ? 'parchment' : 'dark';
  document.body.setAttribute('data-theme', current);
  localStorage.setItem('theme', current);
  btn.textContent = current === 'dark' ? 'Light Mode' : 'Dark Mode';
  btn.setAttribute('aria-pressed', current === 'dark');
  btn.setAttribute('aria-label', current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  });
}

// Initial load and event bindings
let questsChannel = null;
async function initApp() {
  if (!(await enforceAllianceOrAdminAccess())) return;
  bindUI();
  initThemeToggle();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;
  let canStart = false;
  try {
  const res = await authFetch('/api/alliance-members/view');
  const json = res.ok ? await res.json() : {};
  const me = (json.alliance_members || []).find(m => m.user_id === user.id);
  if (window.user?.is_admin || me?.permissions?.can_manage_quests || ['Leader','Elder'].includes(me?.rank)) {
  canStart = true;
  }
  } catch (err) {
  console.error('Permission lookup failed', err);
  }
  const startBtn = document.getElementById('start-new-quest');
  if (startBtn) {
  startBtn.disabled = !canStart;
  if (!canStart) startBtn.style.display = 'none';
  }
  const { data: alliance } = await supabase
  .from('users')
  .select('alliance_id')
  .eq('user_id', user.id)
  .single();
  if (alliance?.alliance_id) initRealtime(alliance.alliance_id);
  supabase.auth.onAuthStateChange(() => {
  if (questsChannel) {
  supabase.removeChannel(questsChannel);
  questsChannel = null;
  }
  });
  const lastTab = safeStorage('lastTab', v => ['active','completed','expired'].includes(v), 'active');
  document.querySelectorAll('.filter-tab').forEach(b => {
  b.classList.remove('active');
  b.setAttribute('aria-pressed', 'false');
  });
  const btn = document.querySelector(`.filter-tab[data-filter="${lastTab}"]`);
  if (btn) {
  btn.classList.add('active');
  btn.setAttribute('aria-pressed', 'true');
  }
  loadQuests(lastTab);
  loadHeroes();
}
document.addEventListener('DOMContentLoaded', initApp);

function initRealtime(aid) {
  if (questsChannel) {
  supabase.removeChannel(questsChannel);
  questsChannel = null;
  }

  let attempts = 0;
  const connect = () => {
  questsChannel = supabase
  .channel('public:quest_alliance_tracking')
  .on(
  'postgres_changes',
  { event: '*', schema: 'public', table: 'quest_alliance_tracking', filter: `alliance_id=eq.${aid}` },
  () => {
  const active = document.querySelector('.filter-tab.active')?.dataset.filter || 'active';
  loadQuests(active);
  }
  )
  .on('close', reconnect)
  .on('error', reconnect)
  .subscribe(status => {
  if (status === 'SUBSCRIBED') attempts = 0;
  });
  };

  const reconnect = () => {
  attempts += 1;
  const delay = Math.min(30000, 1000 * 2 ** attempts);
  setTimeout(connect, delay);
  };

  connect();

  window.addEventListener('beforeunload', async () => {
  if (questsChannel) {
  await supabase.removeChannel(questsChannel);
  questsChannel = null;
  }
  });
}
