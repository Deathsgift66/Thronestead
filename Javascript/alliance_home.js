// Project Name: Thronestead©
// File Name: alliance_home.js
// Version 6.14.2025.20.12
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML, setText, formatDate, fragmentFrom, jsonFetch } from './utils.js';

let activityChannel = null;

// Clean up realtime connections when leaving the page
window.addEventListener('beforeunload', () => {
  if (activityChannel) supabase.removeChannel(activityChannel);
});

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user?.id) {
    window.location.href = 'login.html';
    return;
  }
  fetchAllianceDetails(session.user.id);
});

/**
 * Fetch alliance details via REST then initialize realtime channel.
 * @param {string} userId Authenticated user identifier
 */
async function fetchAllianceDetails(userId) {
  try {
    const data = await jsonFetch('/api/alliance-home/details', {
      headers: { 'X-User-ID': userId }
    });
    populateAlliance(data);
    setupRealtime(data.alliance?.alliance_id);
  } catch (err) {
    console.error('Failed to fetch alliance details:', err);
  }
}

function populateAlliance(data) {
  const a = data.alliance;
  if (!a) return;

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
    banner.src = a.banner || 'Assets/banner.png';
    banner.alt = `Banner of ${a.name}`;
  }

  const emblem = document.getElementById('alliance-emblem-img');
  if (emblem) emblem.alt = `Emblem of ${a.name}`;

  if (data.vault) {
    setText('alliance-fortification', data.vault.fortification_level ?? 0);
    setText('alliance-army', data.vault.army_count ?? 0);
    setText('vault-gold', data.vault.gold ?? 0);
    setText('vault-food', data.vault.food ?? 0);
    setText('vault-ore', data.vault.iron_ore ?? 0);
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

// === Render Functions ===

/**
 * Render active alliance projects with progress bars.
 * @param {Array} projects Project list
 */
function renderProjects(projects = []) {
  const container = document.getElementById('project-progress-bars');
  if (!container) return;
  if (!projects.length) {
    container.innerHTML = '<p class="empty">No active projects.</p>';
    return;
  }
  const frag = fragmentFrom(projects, p => {
    const div = document.createElement('div');
    div.className = 'progress-bar';
    div.innerHTML = `\n    <label>${escapeHTML(p.name)}</label>\n    <progress value="${p.progress}" max="100"></progress>\n    <span>${p.progress}%</span>\n  `;
    return div;
  });
  container.replaceChildren(frag);
}

/**
 * Render alliance member table.
 * @param {Array} members Member list
 */
function renderMembers(members = []) {
  const body = document.getElementById('members-list');
  if (!body) return;
  if (!members.length) {
    body.innerHTML = '<tr><td class="empty" colspan="5">No members.</td></tr>';
    return;
  }
  const highest = Math.max(0, ...members.map(m => m.contribution || 0));
  const frag = fragmentFrom(members, m => {
    const row = document.createElement('tr');
    let icons = '';
    const rank = String(m.rank || '').toLowerCase();
    if (rank === 'leader') icons += '👑 ';
    else if (rank === 'officer') icons += '🛡️ ';
    if ((m.contribution || 0) === highest && highest > 0) icons += '🔥 ';
    row.innerHTML = `
      <td>${icons}<img src="../images/crests/${escapeHTML(m.crest || 'default.png')}" alt="Crest of ${escapeHTML(m.username)}" class="crest"></td>
      <td>${escapeHTML(m.username)}</td>
      <td>${escapeHTML(m.rank)}</td>
      <td>${m.contribution ?? 0}</td>
      <td>${escapeHTML(m.status)}</td>`;
    return row;
  });
  body.replaceChildren(frag);
}

function renderTopContributors(members = []) {
  const list = document.getElementById('top-contrib-list');
  if (!list) return;
  list.innerHTML = '';
  if (!members.length) {
    list.innerHTML = '<p class="empty">No contributors yet.</p>';
    return;
  }

  const top = [...members]
    .sort((a, b) => (b.contribution || 0) - (a.contribution || 0))
    .slice(0, 5);

  top.forEach(m => {
    const li = document.createElement('li');
    li.className = 'top-contrib-entry';

    const img = document.createElement('img');
    img.className = 'contrib-avatar';
    img.src = m.avatar || 'Assets/avatars/default_avatar_emperor.png';
    img.alt = m.username;
    li.appendChild(img);

    const span = document.createElement('span');
    span.textContent = ` ${m.username} - ${m.contribution}`;
    li.appendChild(span);

    list.appendChild(li);
  });
}

function renderQuests(quests = []) {
  const container = document.getElementById('quest-list');
  if (!container) return;
  container.innerHTML = '';
  if (!quests.length) {
    container.innerHTML = '<p class="empty">No active quests.</p>';
    return;
  }
  quests.forEach(q => {
    const card = document.createElement('div');
    card.className = 'quest-card';
    card.innerHTML = `<strong>${escapeHTML(q.name)}</strong><div class="quest-progress-bar"><div class="quest-progress-fill" style="width:${q.progress}%"></div></div>`;
    container.appendChild(card);
  });
}

function renderAchievements(achievements = []) {
  const list = document.getElementById('achievements-list');
  if (!list) return;
  if (!achievements.length) {
    list.innerHTML = '<p class="empty">No achievements earned yet.</p>';
    return;
  }
  list.innerHTML = '';
  achievements.forEach(a => {
    const li = document.createElement('li');
    const badge = document.createElement('span');
    badge.className = 'achievement-badge';
    if (a.badge_icon_url) badge.style.backgroundImage = `url(${a.badge_icon_url})`;
    li.appendChild(badge);
    li.insertAdjacentText('beforeend', ` ${a.name}`);
    list.appendChild(li);
  });
}

/**
 * Render recent alliance activity feed.
 * @param {Array} entries Activity log entries
 */
function renderActivity(entries = []) {
  const list = document.getElementById('activity-log');
  if (!list) return;
  if (!entries.length) {
    list.innerHTML = '<p class="empty">No recent activity.</p>';
    return;
  }
  const frag = fragmentFrom(entries, e => {
    const li = document.createElement('li');
    li.className = 'activity-log-entry';
    li.textContent = `[${formatDate(e.created_at)}] ${e.username}: ${e.description}`;
    return li;
  });
  list.replaceChildren(frag);
}

function renderDiplomacy(treaties = []) {
  const container = document.getElementById('diplomacy-table');
  if (!container) return;
  container.innerHTML = '';
  if (!treaties.length) {
    container.innerHTML = '<p class="empty">No treaties.</p>';
    return;
  }
  treaties.forEach(t => {
    const row = document.createElement('div');
    row.className = 'diplomacy-row';
    row.textContent = `${t.treaty_type} with Alliance ${t.partner_alliance_id} (${t.status})`;
    container.appendChild(row);
  });
}

function renderActiveBattles(wars = []) {
  const container = document.getElementById('active-battles-list');
  if (!container) return;
  container.innerHTML = '';

  const active = wars.filter(w => w.war_status === 'active');
  if (!active.length) {
    container.innerHTML = '<p class="empty">No active battles.</p>';
    return;
  }
  const frag = fragmentFrom(active, w => {
    const div = document.createElement('div');
    div.className = 'battle-entry';
    div.textContent = `War ${w.alliance_war_id} — ${w.war_status}`;
    return div;
  });
  container.appendChild(frag);
}

function renderWarScore(wars = []) {
  const container = document.getElementById('war-score-summary');
  if (!container) return;
  container.innerHTML = '';
  if (!wars.length) {
    container.innerHTML = '<p class="empty">No war scores.</p>';
    return;
  }
  const frag = fragmentFrom(wars, w => {
    const div = document.createElement('div');
    const att = w.attacker_score ?? 0;
    const def = w.defender_score ?? 0;
    div.textContent = `War ${w.alliance_war_id}: Attacker ${att} vs Defender ${def}`;
    return div;
  });
  container.appendChild(frag);
}

// === Realtime Activity Logging ===

/**
 * Subscribe to alliance activity feed via Supabase realtime.
 * @param {number|string} allianceId Alliance identifier
 */
function setupRealtime(allianceId) {
  if (!allianceId) return;
  if (activityChannel) supabase.removeChannel(activityChannel);

  activityChannel = supabase
    .channel(`alliance_home_${allianceId}`)
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'alliance_activity_log',
        filter: `alliance_id=eq.${allianceId}`
      },
      payload => addActivityEntry(payload.new)
    )
    .subscribe();
}

/**
 * Prepend an activity entry to the log, keeping the last 20 entries.
 * @param {object} entry Activity payload
 */
function addActivityEntry(entry) {
  const list = document.getElementById('activity-log');
  if (!list) return;
  const li = document.createElement('li');
  li.className = 'activity-log-entry';
  li.textContent = `[${formatDate(entry.created_at)}] ${entry.user_id}: ${entry.description}`;
  list.prepend(li);
  if (list.children.length > 20) list.removeChild(list.lastChild);
}
