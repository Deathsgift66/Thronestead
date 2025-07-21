// Project Name: Thronestead©
// File Name: alliance_home.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from './supabaseClient.js';
import {
  escapeHTML,
  setText,
  formatDate,
  fragmentFrom,
  setFallbackText,
  jsonFetch,
  showToast,
  authFetch,
  debounce,
  setBarWidths
} from './utils.js';
import { refreshSessionAndStore } from './auth.js';

let activityChannel = null;

let cachedAllianceDetails = null;
let membersLoading = false;
let activityLoading = false;
let currentAllianceId = null;

const ASSET_BASE_URL = '/Assets';
const DEFAULT_AVATAR = `${ASSET_BASE_URL}/avatars/default_avatar_emperor.png`;
const DEFAULT_BANNER = `${ASSET_BASE_URL}/banner.png`;
const THRONESTEAD = (window.__thronestead = window.__thronestead || {});

function setupCleanup() {
  window.addEventListener('beforeunload', async () => {
    if (activityChannel) {
      await supabase.removeChannel(activityChannel).catch(console.error);
    }
  });
}

const LIMIT = 50;
const ACTIVITY_LIMIT = 20;
let membersOffset = 0;
let activityOffset = 0;
const pendingEntries = [];
let flushTimer = null;
let realtimeDelay = 1000;

function resetOffsets() {
  membersOffset = 0;
  activityOffset = 0;
}

async function fetchAllianceId(userId) {
  const { data, error } = await supabase
    .from('users')
    .select('alliance_id')
    .eq('user_id', userId)
    .single();
  if (error) throw error;
  return data.alliance_id;
}

async function jsonFetchRetry(url, opts = {}, retries = 2) {
  for (let i = 0; i <= retries; i++) {
    try {
      return await jsonFetch(url, opts);
    } catch (err) {
      if (i === retries) throw err;
      await new Promise(r => setTimeout(r, 500 * 2 ** i));
    }
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  setupCleanup();
  let session;
  try {
    const res = await supabase.auth.getSession();
    session = res.data?.session;
  } catch (err) {
    console.error('❌ Session fetch failed:', err);
    showToast('Authentication failed. Please log in again.', 'error');
    window.location.href = 'login.html';
    return;
  }

  if (!session?.user?.id) {
    showToast('Please log in to continue.', 'error');
    window.location.href = 'login.html';
    return;
  }

  try {
    currentAllianceId = await fetchAllianceId(session.user.id);
  } catch (err) {
    console.error('Alliance lookup failed:', err);
    showToast('Unable to verify alliance.', 'error');
    return;
  }

  let cached = sessionStorage.getItem('lastAllianceDetails');
  if (cached) {
    try {
      populateAlliance(JSON.parse(cached));
    } catch (e) {
      console.warn('Failed to parse cached alliance details:', e);
    }
  }

  const first = await fetchAllianceDetails();
  membersOffset = first.members.length;
  activityOffset = first.activity.length;
  await cacheUserPermissions(session.user.id);

  document
    .getElementById('load-more-members')
    ?.addEventListener('click', debounce(loadMoreMembers, 300));
  document
    .getElementById('load-more-activity')
    ?.addEventListener('click', debounce(loadMoreActivity, 300));
});

async function fetchAllianceDetails(offset = 0) {
  try {
    if (offset === 0) resetOffsets();
    const data = await jsonFetchRetry(
      `/api/alliance-home/details?limit=${LIMIT}&offset=${offset}`
    );
    if (offset === 0 && data.alliance && data.alliance.alliance_id !== currentAllianceId) {
      showToast('Alliance mismatch.', 'error');
      return data;
    }
    if (offset === 0) {
      const str = JSON.stringify(data);
      sessionStorage.setItem('lastAllianceDetails', str);
      cachedAllianceDetails = data;
      if (data.alliance?.alliance_id) currentAllianceId = data.alliance.alliance_id;
    } else {
      cachedAllianceDetails = data;
    }
    populateAlliance(data, offset === 0);
    if (offset === 0) setupRealtime(currentAllianceId);
    toggleButton('load-more-members', data.members.length === LIMIT);
    toggleButton('load-more-activity', data.activity.length === ACTIVITY_LIMIT);
    return data;
  } catch (err) {
    console.error('❌ Failed to fetch alliance details:', err);
    const msg = navigator.onLine ? 'Failed to load alliance data.' : 'You appear to be offline.';
    showToast(msg, 'error');
    throw err;
  }
}

function safeRender(fn, ...args) {
  try { fn(...args); } catch (err) { console.error(`Render failed: ${fn.name}`, err); }
}

const safeUsername = m => escapeHTML(m.username || 'Alliance Member');

function populateAlliance(data, initial = true) {
  const a = data.alliance;
  if (!a) return;

  const safe = v => v ?? 0;

  setText('alliance-name', a.name);
  setText('alliance-leader', a.leader);
  setText('alliance-region', a.region);
  setText('alliance-founded', formatDate(a.created_at));
  setText('alliance-level', a.level);
  setText('alliance-status', a.status);
  setText('alliance-members', a.member_count);
  setText('alliance-wars-count', a.wars_count);
  setText('alliance-treaties-count', a.treaties_count);
  setText('alliance-military', a.military_score);
  setText('alliance-economy', a.economy_score);
  setText('alliance-diplomacy', a.diplomacy_score);

  const banner = document.getElementById('alliance-banner-img');
  if (banner) {
    banner.src = a.banner || DEFAULT_BANNER;
    banner.alt = `Banner of ${a.name}`;
    banner.onerror = () => (banner.src = DEFAULT_BANNER);
  }

  const emblem = document.getElementById('alliance-emblem-img');
  if (emblem) {
    emblem.src = a.emblem_url || DEFAULT_AVATAR;
    emblem.alt = `Emblem of ${a.name}`;
    emblem.onerror = () => (emblem.src = DEFAULT_AVATAR);
  }

  if (data.vault) {
    setText('alliance-fortification', safe(data.vault.fortification_level));
    setText('alliance-army', safe(data.vault.army_count));
    setText('vault-gold', safe(data.vault.gold));
    setText('vault-food', safe(data.vault.food));
    setText('vault-ore', safe(data.vault.iron_ore));
  }

  safeRender(renderProjects, data.projects);
  safeRender(renderMembers, data.members, !initial);
  safeRender(renderTopContributors, data.members);
  safeRender(renderQuests, data.quests);
  safeRender(renderAchievements, data.achievements);
  safeRender(renderActivity, data.activity, !initial);
  try {
    renderDiplomacy(data.treaties);
  } catch (e) {
    setFallbackText(document.getElementById('diplomacy-table'), 'Failed to render diplomacy overview.');
  }
  safeRender(renderActiveBattles, data.wars);
  try {
    renderWarScore(data.wars);
  } catch (e) {
    setFallbackText(document.getElementById('war-score-summary'), 'Failed to render war score.');
  }
}

// === Render Utilities ===


function renderProjects(projects = []) {
  const container = document.getElementById('project-progress-bars');
  if (!container) return;
  if (!projects.length) return setFallbackText(container, 'No active projects.');
  const frag = fragmentFrom(projects, p => {
    const div = document.createElement('div');
    div.className = 'progress-bar';
    div.innerHTML = `<label>${escapeHTML(p.name)}</label><progress value="${p.progress}" max="100"></progress><span>${p.progress}%</span>`;
    return div;
  });
  container.replaceChildren(frag);
}

function renderMembers(members = [], append = false) {
  const body = document.getElementById('members-list');
  if (!body) return;
  if (!members.length && !append) return setFallbackText(body, 'No members.', 'tr');

  const top = Math.max(0, ...members.map(m => m.contribution || 0));
  const frag = fragmentFrom(members, m => {
    const row = document.createElement('tr');
    row.tabIndex = -1;
    let icons = '';
    if (m.rank === 'Leader') icons += '<span title="Leader">👑</span> ';
    else if (m.rank === 'Officer') icons += '<span title="Officer">🛡️</span> ';
    if ((m.contribution || 0) === top && top > 0) icons += '<span title="Top Contributor">🔥</span> ';
    const name = safeUsername(m);
    row.innerHTML = `
  <td>${icons}<picture><source srcset="${ASSET_BASE_URL}/crests/${escapeHTML(m.crest || 'default.webp')}" type="image/webp"><img src="${ASSET_BASE_URL}/crests/${escapeHTML(m.crest || 'default.png')}" alt="Crest of ${name}" class="crest" loading="lazy" decoding="async"></picture></td>
  <td>${name}</td>
  <td>${escapeHTML(m.rank)}</td>
  <td>${m.contribution ?? 0}</td>
  <td>${escapeHTML(m.status)}</td>`;
    return row;
  });
  if (append) body.appendChild(frag);
  else body.replaceChildren(frag);
}

function renderTopContributors(members = []) {
  const list = document.getElementById('top-contrib-list');
  if (!list) return;
  list.innerHTML = '';

  if (!members.length) return setFallbackText(list, 'No contributors yet.');

  members
    .sort((a, b) => (b.contribution || 0) - (a.contribution || 0))
    .slice(0, 5)
    .forEach(m => {
      const li = document.createElement('li');
      li.className = 'top-contrib-entry';
      const name = safeUsername(m);
      const avatarSrc = m.avatar || DEFAULT_AVATAR;
      const altText = m.avatar ? `${name}'s avatar` : `Default avatar for ${name}`;
      let badge = '';
      if (m.rank === 'Leader') badge = '<span title="Leader">👑</span> ';
      else if (m.rank === 'Officer') badge = '<span title="Officer">🛡️</span> ';
      li.innerHTML = `
    <img class="contrib-avatar" src="${avatarSrc}" alt="${altText}" loading="lazy" decoding="async">
    <span> ${badge}${name} - ${m.contribution}</span>`;
      list.appendChild(li);
    });
}

function renderQuests(quests = []) {
  const container = document.getElementById('quest-list');
  if (!container) return;
  if (!quests.length) return setFallbackText(container, 'No active quests.');

  const frag = fragmentFrom(quests, q => {
    const div = document.createElement('div');
    div.className = 'quest-card';
    div.innerHTML = `<strong>${escapeHTML(q.name)}</strong><div class="quest-progress-bar"><div class="quest-progress-fill" data-width="${q.progress}"></div></div>`;
    return div;
  });
  container.replaceChildren(frag);
  setBarWidths(container);
}

function renderAchievements(achievements = []) {
  const list = document.getElementById('achievements-list');
  if (!list) return;
  if (!achievements.length) return setFallbackText(list, 'No achievements earned yet.');

  const frag = fragmentFrom(achievements, a => {
    const li = document.createElement('li');
    const badge = document.createElement('span');
    badge.className = 'achievement-badge';
    if (a.badge_icon_url) badge.style.backgroundImage = `url(${a.badge_icon_url})`;
    li.appendChild(badge);
    li.insertAdjacentText('beforeend', ` ${a.name}`);
    return li;
  });
  list.replaceChildren(frag);
}

function renderActivity(entries = [], append = false) {
  const list = document.getElementById('activity-log');
  if (!list) return;
  if (!entries.length && !append) return setFallbackText(list, 'No recent activity.');

  const frag = fragmentFrom(entries, e => {
    const li = document.createElement('li');
    li.className = 'activity-log-entry';
    li.tabIndex = -1;
    li.setAttribute('role', 'listitem');
    li.textContent = `[${formatDate(e.created_at)}] ${escapeHTML(e.username)}: ${escapeHTML(e.description)}`;
    return li;
  });
  if (append) list.appendChild(frag);
  else list.replaceChildren(frag);
  pruneActivityLog(list);
}

function renderDiplomacy(treaties = []) {
  const container = document.getElementById('diplomacy-table');
  if (!container) return;
  if (!treaties.length) return setFallbackText(container, 'No treaties.');
  const frag = fragmentFrom(treaties, t => {
    const div = document.createElement('div');
    div.className = 'diplomacy-row';
    div.textContent = `${escapeHTML(t.treaty_type)} with Alliance ${t.partner_alliance_id} (${escapeHTML(t.status)})`;
    return div;
  });
  container.replaceChildren(frag);
}

function renderActiveBattles(wars = []) {
  const container = document.getElementById('active-battles-list');
  if (!container) return;

  const active = wars.filter(w => w.war_status === 'active');
  if (!active.length) return setFallbackText(container, 'No active battles.');

  const frag = fragmentFrom(active, w => {
    const div = document.createElement('div');
    div.className = 'battle-entry';
    div.textContent = `War ${w.alliance_war_id} — ${escapeHTML(w.war_status)}`;
    return div;
  });
  container.replaceChildren(frag);
}

function renderWarScore(wars = []) {
  const container = document.getElementById('war-score-summary');
  if (!container) return;
  if (!wars.length) return setFallbackText(container, 'No war scores.');

  const frag = fragmentFrom(wars, w => {
    const div = document.createElement('div');
    const att = w.attacker_score ?? 0;
    const def = w.defender_score ?? 0;
    div.textContent = `War ${w.alliance_war_id}: Attacker ${att} vs Defender ${def}`;
    return div;
  });
  container.replaceChildren(frag);
}

// === Realtime Handling ===

async function setupRealtime(allianceId) {
  if (!allianceId) return;
  if (activityChannel) await supabase.removeChannel(activityChannel).catch(console.error);

  activityChannel = supabase
    .channel(`alliance_home_${allianceId}`)
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'alliance_activity_log',
      filter: `alliance_id=eq.${allianceId}`
    }, payload => addActivityEntry(payload.new))
    .on('error', () => handleRealtimeError(allianceId))
    .on('close', () => handleRealtimeError(allianceId))
    .subscribe()
    .then(() => { realtimeDelay = 1000; })
    .catch(err => handleRealtimeError(allianceId, err));
}

function handleRealtimeError(allianceId) {
  console.warn('Realtime channel error. Reconnecting...');
  const delay = realtimeDelay;
  realtimeDelay = Math.min(realtimeDelay * 2, 30000);
  setTimeout(() => setupRealtime(allianceId), delay);
}

function addActivityEntry(entry) {
  pendingEntries.push(entry);
  if (!flushTimer) flushTimer = setTimeout(flushActivityEntries, 1000);
}

function flushActivityEntries() {
  const render = () => {
    const list = document.getElementById('activity-log');
    if (!list || !pendingEntries.length) {
      pendingEntries.length = 0;
      flushTimer = null;
      return;
    }
    const frag = fragmentFrom(pendingEntries, e => {
      const li = document.createElement('li');
      li.className = 'activity-log-entry';
      li.tabIndex = -1;
      li.setAttribute('role', 'listitem');
      const actor = escapeHTML(e.username || e.user_id);
      li.textContent = `[${formatDate(e.created_at)}] ${actor}: ${escapeHTML(e.description)}`;
      return li;
    });
    list.prepend(frag);
    pruneActivityLog(list);
    pendingEntries.length = 0;
    flushTimer = null;
  };

  if ('requestIdleCallback' in window) requestIdleCallback(render);
  else setTimeout(render, 0);
}

function pruneActivityLog(list, limit = 20) {
  while (list.children.length > limit) list.removeChild(list.lastChild);
}

async function loadMoreMembers() {
  if (membersLoading) return;
  membersLoading = true;
  const btn = document.getElementById('load-more-members');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span> Loading...';
  }
  try {
    const data = await fetchAllianceDetails(membersOffset);
    renderMembers(data.members, true);
    membersOffset += data.members.length;
    toggleButton('load-more-members', data.members.length === LIMIT);
    const rows = document.getElementById('members-list')?.querySelectorAll('tr');
    if (rows && rows.length) rows[rows.length - data.members.length]?.focus?.();
  } catch (err) {
    console.error('❌ Failed to load more members:', err);
    showToast('Unable to load more members.', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Load More';
    }
    membersLoading = false;
  }
}

async function loadMoreActivity() {
  if (activityLoading) return;
  activityLoading = true;
  const btn = document.getElementById('load-more-activity');
  const list = document.getElementById('activity-log');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span> Loading...';
  }
  if (list) list.setAttribute('aria-busy', 'true');
  try {
    const data = await jsonFetchRetry(`/api/alliance-home/details?limit=${ACTIVITY_LIMIT}&offset=${activityOffset}`);
    const entries = data.activity || [];
    renderActivity(entries, true);
    activityOffset += entries.length;
    toggleButton('load-more-activity', entries.length === ACTIVITY_LIMIT);
    if (list) list.lastElementChild?.previousElementSibling?.focus?.();
  } catch (err) {
    console.error('❌ Failed to load activity:', err);
    showToast('Unable to load more activity.', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Load More';
    }
    if (list) list.setAttribute('aria-busy', 'false');
    activityLoading = false;
  }
}

const PERMISSIONS_CACHE_MS = 60 * 60 * 1000;

async function cacheUserPermissions(userId) {
  if (!userId) return;
  const cached = sessionStorage.getItem('userPermissions');
  const ts = parseInt(sessionStorage.getItem('userPermissionsTs') || '0', 10);
  if (cached && Date.now() - ts < PERMISSIONS_CACHE_MS) {
    THRONESTEAD.user = THRONESTEAD.user || {};
    THRONESTEAD.user.permissions = JSON.parse(cached);
    return;
  }
  try {
    const res = await authFetch('/api/alliance-members/view');
    const json = await res.json();
    const me = (json.alliance_members || []).find(m => m.user_id === userId);
    if (me && me.permissions) {
      THRONESTEAD.user = THRONESTEAD.user || {};
      THRONESTEAD.user.permissions = me.permissions;
      sessionStorage.setItem('userPermissions', JSON.stringify(me.permissions));
      sessionStorage.setItem('userPermissionsTs', Date.now().toString());
    }
  } catch (err) {
    console.error('Failed to cache permissions:', err);
    await refreshSessionAndStore();
  }
}

function toggleButton(id, show) {
  const btn = document.getElementById(id);
  if (!btn) return;
  btn.classList.toggle('hidden', !show);
}
