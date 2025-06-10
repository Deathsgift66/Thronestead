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

  const { data: userData } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', user.id)
    .single();

  if (!userData) return;

  await loadFullHistory(user.id, userData.kingdom_id);
  bindCollapsibles();
}

async function loadFullHistory(userId, kingdomId) {
  const res = await fetch(`/api/kingdom-history/${kingdomId}/full`, {
    headers: { 'X-User-ID': userId }
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
    });
  });
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
