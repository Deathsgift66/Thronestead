// Project Name: Thronestead©
// File Name: alliance_home.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { escapeHTML, setText, formatDate, fragmentFrom, jsonFetch } from './utils.js';

const DEFAULT_BANNER = '/Assets/banner.png';
const LIMIT = 50;
let sessionData = null;
let activityChannel = null;
let membersOffset = 0;
let activityOffset = 0;
let warsOffset = 0;

async function applyAllianceAppearance() {
  try {
    if (!sessionData) return;
    const res = await fetch('/api/alliance-home/details', {
      headers: { Authorization: `Bearer ${sessionData.access_token}` }
    });
    if (!res.ok) return;
    const { alliance } = await res.json();
    if (!alliance) return;

    const banner = alliance.banner || DEFAULT_BANNER;
    const emblem = alliance.emblem_url;

    document.querySelectorAll('.alliance-banner').forEach(img => {
      img.src = banner;
      img.onerror = () => (img.src = '/Assets/fallback.png');
    });

    if (emblem) {
      document.querySelectorAll('.alliance-emblem').forEach(img => {
        img.src = emblem;
        img.onerror = () => (img.src = '/Assets/fallback.png');
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
    console.error('❌ Failed to apply alliance appearance:', err);
  }
}

window.addEventListener('beforeunload', () => {
  if (activityChannel) supabase.removeChannel(activityChannel);
});

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } = {} } = await supabase.auth.getSession();
  const userId = session?.user?.id;
  if (!userId) {
    window.location.href = 'login.html';
    return;
  }
  sessionData = session;
  applyAllianceAppearance();
  const data = await fetchAllianceDetails();
  populateAlliance(data);
  setupRealtime(data.alliance?.alliance_id);
  membersOffset = data.members.length;
  activityOffset = data.activity.length;
  warsOffset = data.wars.length;
  updateLoadButtons(data);
  document.getElementById('load-more-members')?.addEventListener('click', loadMoreMembers);
  document.getElementById('load-more-activity')?.addEventListener('click', loadMoreActivity);
  document.getElementById('load-more-wars')?.addEventListener('click', loadMoreWars);
});

async function fetchAllianceDetails(offset = 0) {
  const data = await jsonFetch(`/api/alliance-home/details?limit=${LIMIT}&offset=${offset}`, {
    headers: { Authorization: `Bearer ${sessionData.access_token}` }
  });
  return data;
}

function populateAlliance(data) {
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
    banner.src = a.banner || '/Assets/banner.png';
    banner.onerror = () => (banner.src = '/Assets/fallback.png');
    banner.alt = `Banner of ${a.name}`;
  }

  const emblem = document.getElementById('alliance-emblem-img');
  if (emblem) {
    emblem.onerror = () => (emblem.src = '/Assets/fallback.png');
    emblem.alt = `Emblem of ${a.name}`;
  }

  if (data.vault) {
    setText('alliance-fortification', safe(data.vault.fortification_level));
    setText('alliance-army', safe(data.vault.army_count));
    setText('vault-gold', safe(data.vault.gold));
    setText('vault-food', safe(data.vault.food));
    setText('vault-ore', safe(data.vault.iron_ore));
  }

  renderProjects(data.projects);
  renderMembers(data.members);
  renderTopContributors(data.members);
  renderQuests(data.quests);
  renderAchievements(data.achievements);
  renderActivity(data.activity);
  renderDiplomacy(data.treaties);
  renderActiveBattles(data.wars);
  renderWarScore(data.wars);
}

// === Render Utilities ===

function setFallbackText(el, message, tag = 'p') {
  el.innerHTML = `<${tag} class="empty">${message}</${tag}>`;
}

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
    let icons = '';
    if (m.rank === 'Leader') icons += '👑 ';
    else if (m.rank === 'Officer') icons += '🛡️ ';
    if ((m.contribution || 0) === top && top > 0) icons += '🔥 ';
    row.innerHTML = `
      <td>${icons}<img src="../assets/crests/${escapeHTML(m.crest || 'default.png')}" alt="Crest of ${escapeHTML(m.username)}" class="crest"></td>
      <td>${escapeHTML(m.username)}</td>
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
      li.innerHTML = `
        <img class="contrib-avatar" src="${m.avatar || '/Assets/avatars/default_avatar_emperor.png'}" alt="${escapeHTML(m.username)}">
        <span> ${escapeHTML(m.username)} - ${m.contribution}</span>`;
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
    li.textContent = `[${formatDate(e.created_at)}] ${e.username}: ${e.description}`;
    return li;
  });
  if (append) list.appendChild(frag);
  else list.replaceChildren(frag);
}

function renderDiplomacy(treaties = []) {
  const container = document.getElementById('diplomacy-table');
  if (!container) return;
  if (!treaties.length) return setFallbackText(container, 'No treaties.');
  const frag = fragmentFrom(treaties, t => {
    const div = document.createElement('div');
    div.className = 'diplomacy-row';
    div.textContent = `${t.treaty_type} with Alliance ${t.partner_alliance_id} (${t.status})`;
    return div;
  });
  container.replaceChildren(frag);
}

function renderActiveBattles(wars = [], append = false) {
  const container = document.getElementById('active-battles-list');
  if (!container) return;

  const active = wars.filter(w => w.war_status === 'active');
  if (!active.length && !append) return setFallbackText(container, 'No active battles.');

  const frag = fragmentFrom(active, w => {
    const div = document.createElement('div');
    div.className = 'battle-entry';
    div.textContent = `War ${w.alliance_war_id} — ${w.war_status}`;
    return div;
  });
  if (append) container.appendChild(frag);
  else container.replaceChildren(frag);
}

function renderWarScore(wars = [], append = false) {
  const container = document.getElementById('war-score-summary');
  if (!container) return;
  if (!wars.length && !append) return setFallbackText(container, 'No war scores.');

  const frag = fragmentFrom(wars, w => {
    const div = document.createElement('div');
    const att = w.attacker_score ?? 0;
    const def = w.defender_score ?? 0;
    div.textContent = `War ${w.alliance_war_id}: Attacker ${att} vs Defender ${def}`;
    return div;
  });
  if (append) container.appendChild(frag);
  else container.replaceChildren(frag);
}

// === Realtime Handling ===

function setupRealtime(allianceId) {
  if (!allianceId) return;
  if (activityChannel) supabase.removeChannel(activityChannel);

  activityChannel = supabase
    .channel(`alliance_home_${allianceId}`)
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'alliance_activity_log',
      filter: `alliance_id=eq.${allianceId}`
    }, payload => addActivityEntry(payload.new))
    .subscribe();
}

function addActivityEntry(entry) {
  const list = document.getElementById('activity-log');
  if (!list) return;

  const li = document.createElement('li');
  li.className = 'activity-log-entry';
  li.textContent = `[${formatDate(entry.created_at)}] ${entry.user_id}: ${entry.description}`;
  list.prepend(li);

  if (list.children.length > 20) list.removeChild(list.lastChild);
}

async function loadMoreMembers() {
  const data = await fetchAllianceDetails(membersOffset);
  renderMembers(data.members, true);
  membersOffset += data.members.length;
  toggleButton('load-more-members', data.members.length === LIMIT);
}

async function loadMoreActivity() {
  const data = await fetchAllianceDetails(activityOffset);
  renderActivity(data.activity, true);
  activityOffset += data.activity.length;
  toggleButton('load-more-activity', data.activity.length === LIMIT);
}

async function loadMoreWars() {
  const data = await fetchAllianceDetails(warsOffset);
  renderActiveBattles(data.wars, true);
  renderWarScore(data.wars, true);
  warsOffset += data.wars.length;
  toggleButton('load-more-wars', data.wars.length === LIMIT);
}

function updateLoadButtons(data) {
  toggleButton('load-more-members', data.members.length === LIMIT);
  toggleButton('load-more-activity', data.activity.length === LIMIT);
  toggleButton('load-more-wars', data.wars.length === LIMIT);
}

function toggleButton(id, show) {
  const btn = document.getElementById(id);
  if (btn) btn.style.display = show ? 'block' : 'none';
}
