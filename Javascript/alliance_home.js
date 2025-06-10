import { supabase } from './supabaseClient.js';

let activityChannel;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  fetchAllianceDetails(session.user.id);
});

async function fetchAllianceDetails(userId) {
  try {
    const res = await fetch('/api/alliance-home/details', {
      headers: { 'X-User-Id': userId }
    });
    if (!res.ok) throw new Error('Request failed');
    const data = await res.json();
    populateAlliance(data);
    setupRealtime(data.alliance.alliance_id);
  } catch (err) {
    console.error('Failed to fetch alliance details:', err);
  }
}

function populateAlliance(data) {
  const a = data.alliance;
  if (!a) return;
  setText('alliance-name', a.name);
  setText('alliance-leader', a.leader);
  setText('alliance-status', a.status);
  setText('alliance-members', a.member_count);
  const banner = document.getElementById('alliance-banner-img');
  if (banner) banner.src = a.banner || 'Assets/banner.png';

  renderProjects(data.projects);
  renderMembers(data.members);
  renderQuests(data.quests);
  renderAchievements(data.achievements);
  renderActivity(data.activity);
  renderDiplomacy(data.treaties);
  renderWarScore(data.wars);
}

function renderProjects(projects) {
  const container = document.getElementById('project-progress-bars');
  if (!container) return;
  container.innerHTML = '';
  projects.forEach(p => {
    const div = document.createElement('div');
    div.classList.add('project-bar');
    div.innerHTML = `<label>${p.name}</label><progress value="${p.progress}" max="100"></progress> <span>${p.progress}%</span>`;
    container.appendChild(div);
  });
}

function renderMembers(members) {
  const body = document.getElementById('members-list');
  if (!body) return;
  body.innerHTML = '';
  members.forEach(m => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><img src="../images/crests/${m.crest || 'default.png'}" alt="Crest" class="crest"></td>
      <td>${m.username}</td>
      <td>${m.rank}</td>
      <td>${m.contribution}</td>
      <td>${m.status}</td>`;
    body.appendChild(row);
  });
}

function renderQuests(quests) {
  const container = document.getElementById('quest-list');
  if (!container) return;
  container.innerHTML = '';
  quests.forEach(q => {
    const card = document.createElement('div');
    card.classList.add('quest-card');
    card.innerHTML = `<strong>${q.name}</strong><div class="quest-progress-bar"><div class="quest-progress-fill" style="width:${q.progress}%"></div></div>`;
    container.appendChild(card);
  });
}

function renderAchievements(achievements) {
  const list = document.getElementById('achievements-list');
  if (!list) return;
  list.innerHTML = '';
  if (!achievements.length) {
    list.innerHTML = '<li>No achievements earned yet.</li>';
    return;
  }
  achievements.forEach(a => {
    const li = document.createElement('li');
    const img = document.createElement('span');
    img.classList.add('achievement-badge');
    if (a.icon_url) img.style.backgroundImage = `url(${a.icon_url})`;
    li.appendChild(img);
    li.insertAdjacentText('beforeend', ` ${a.name}`);
    list.appendChild(li);
  });
}

function renderActivity(entries) {
  const list = document.getElementById('activity-log');
  if (!list) return;
  list.innerHTML = '';
  entries.forEach(e => {
    const li = document.createElement('li');
    li.classList.add('activity-log-entry');
    li.textContent = `[${formatDate(e.created_at)}] ${e.username}: ${e.description}`;
    list.appendChild(li);
  });
}

function renderDiplomacy(treaties) {
  const container = document.getElementById('diplomacy-table');
  if (!container) return;
  container.innerHTML = '';
  treaties.forEach(t => {
    const row = document.createElement('div');
    row.classList.add('diplomacy-row');
    row.textContent = `${t.treaty_type} with Alliance ${t.partner_alliance_id} (${t.status})`;
    container.appendChild(row);
  });
}

function renderWarScore(wars) {
  const container = document.getElementById('war-score-summary');
  if (!container) return;
  container.innerHTML = '';
  wars.forEach(w => {
    const div = document.createElement('div');
    div.textContent = `War ${w.alliance_war_id}: ${w.attacker_score} - ${w.defender_score}`;
    container.appendChild(div);
  });
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function formatDate(str) {
  if (!str) return '';
  return new Date(str).toLocaleString();
}

function setupRealtime(aid) {
  if (activityChannel) {
    supabase.removeChannel(activityChannel);
  }
  activityChannel = supabase
    .channel('alliance_home_' + aid)
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'alliance_activity_log', filter: `alliance_id=eq.${aid}` },
      payload => addActivityEntry(payload.new)
    )
    .subscribe();
}

function addActivityEntry(entry) {
  const list = document.getElementById('activity-log');
  if (!list) return;
  const li = document.createElement('li');
  li.classList.add('activity-log-entry');
  li.textContent = `[${formatDate(entry.created_at)}] ${entry.user_id}: ${entry.description}`;
  list.prepend(li);
  if (list.children.length > 20) list.removeChild(list.lastChild);
}
