// Project Name: Thronestead©
// File Name: kingdom_history.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';

let kingdomId = null;
let userId = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return (window.location.href = 'login.html');
  userId = user.id;

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

function formatDate(dateStr) {
  if (!dateStr) return 'Unknown';
  return new Date(dateStr).toLocaleDateString();
}

