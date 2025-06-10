/*
Project Name: Kingmakers Rise Frontend
File Name: kingdom_history.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', init);

async function init() {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;

  const { data: { session } } = await supabase.auth.getSession();
  const authHeaders = session
    ? { 'Authorization': `Bearer ${session.access_token}`, 'X-User-ID': user.id }
    : { 'X-User-ID': user.id };

  const { data: userData } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', user.id)
    .single();

  if (!userData) return;

  await loadFullHistory(authHeaders, userData.kingdom_id);
  bindCollapsibles();
  subscribeToRealtime(userData.kingdom_id);
}

async function loadFullHistory(headers, kingdomId) {
  const res = await fetch(`/api/kingdom-history/${kingdomId}/full`, {
    headers
  });
  const data = await res.json();

  renderTimeline(data.timeline || []);
  renderAchievements(data.achievements || []);
  renderLog('war-log', data.wars_fought || [], e => `War ID ${e.war_id}`);
  renderLog('project-log', data.projects_log || [], e => e.name);
  renderLog('quest-log', data.quests_log || [], e => e.quest_code + ' - ' + e.status);
  renderLog('training-log', data.training_log || [], e => `${e.quantity} ${e.unit_name}`);
}

function renderTimeline(events) {
  const el = document.getElementById('timeline');
  el.innerHTML = '';
  if (!events.length) {
    el.innerHTML = '<li>No events</li>';
    return;
  }
  events.forEach(ev => {
    const li = document.createElement('li');
    li.textContent = `[${new Date(ev.event_date).toLocaleDateString()}] ${ev.event_details}`;
    el.appendChild(li);
  });
}

function renderAchievements(list) {
  const grid = document.getElementById('achievement-grid');
  grid.innerHTML = '';
  list.forEach(a => {
    const div = document.createElement('div');
    div.classList.add('achievement-badge');
    div.textContent = a.name;
    grid.appendChild(div);
  });
}

function renderLog(id, list, formatter) {
  const container = document.getElementById(id);
  container.innerHTML = '';
  list.forEach(entry => {
    const li = document.createElement('li');
    li.textContent = formatter(entry);
    container.appendChild(li);
  });
}

function bindCollapsibles() {
  document.querySelectorAll('.collapsible').forEach(sec => {
    const header = sec.querySelector('h3');
    if (!header) return;
    header.addEventListener('click', () => {
      sec.classList.toggle('open');
      const chev = header.querySelector('.chevron');
      if (chev) {
        chev.textContent = sec.classList.contains('open') ? '▼' : '▶';
      }
    });
  });
}

function subscribeToRealtime(kingdomId) {
  supabase
    .channel('history-' + kingdomId)
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'kingdom_history_log', filter: `kingdom_id=eq.${kingdomId}` },
      payload => addTimelineEntry(payload.new)
    )
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'kingdom_achievements', filter: `kingdom_id=eq.${kingdomId}` },
      payload => addAchievementBadge(payload.new)
    )
    .subscribe();
}

function addTimelineEntry(entry) {
  const li = document.createElement('li');
  li.textContent = `[${new Date(entry.event_date).toLocaleDateString()}] ${entry.event_details}`;
  document.getElementById('timeline').prepend(li);
}

function addAchievementBadge(rec) {
  const div = document.createElement('div');
  div.classList.add('achievement-badge');
  div.textContent = rec.name || rec.achievement_code;
  document.getElementById('achievement-grid').prepend(div);
}

function escapeHTML(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
