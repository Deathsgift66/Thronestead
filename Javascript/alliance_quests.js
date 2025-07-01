// Comment
// Project Name: Thronestead©
// File Name: alliance_quests.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
// Frontend logic for the Alliance Quests board.

import { escapeHTML } from './utils.js';

/**
 * Fetch and render quests for the selected status tab.
 * @param {string} status active|completed|expired
 */
export function loadQuests(status = 'active') {
  fetch(`/api/alliance/quests?status=${status}`)
    .then(res => res.json())
    .then(quests => {
      const board = document.getElementById('quest-board');
      const msg = document.getElementById('no-quests-message');
      board.innerHTML = '';
      if (!quests.length) {
        msg.classList.remove('hidden');
        return;
      }
      msg.classList.add('hidden');
      const frag = document.createDocumentFragment();
      quests.forEach(q => frag.appendChild(renderQuestCard(q)));
      board.appendChild(frag);
      initCountdowns();
    })
    .catch(() => {
      document.getElementById('quest-board').textContent = 'Failed to load quests.';
    });
}

// Bind tab clicks
document.querySelectorAll('.filter-tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    loadQuests(btn.dataset.filter);
  });
});

// Open quest modal when a card button is clicked
const boardEl = document.getElementById('quest-board');
boardEl.addEventListener('click', e => {
  const card = e.target.closest('.view-quest-btn');
  if (!card) return;
  openQuestModal(card.dataset.id);
});

// Close modal with button or Escape key
const modalEl = document.getElementById('quest-modal');
modalEl.querySelector('.close-button').addEventListener('click', () => modalEl.classList.remove('visible'));
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') modalEl.classList.remove('visible');
});

/**
 * Render a quest preview card.
 */
function renderQuestCard(q) {
  const div = document.createElement('div');
  div.className = 'quest-card';
  div.innerHTML = `
    <h3 class="quest-title">${escapeHTML(q.name)}</h3>
    <p>${escapeHTML(q.description)}</p>
    <p>Ends in: <span data-end-time="${q.ends_at || ''}">--:--:--</span></p>
    <button class="view-quest-btn" data-id="${q.id || q.quest_code}">View</button>
  `;
  return div;
}

/**
 * Populate and display the quest modal.
 */
function openQuestModal(id) {
  fetch(`/api/alliance/quests/${id}`)
    .then(res => res.json())
    .then(q => {
      document.getElementById('modal-quest-title').textContent = q.name;
      document.getElementById('modal-quest-description').textContent = q.description;
      document.getElementById('modal-time-left').textContent = formatDuration(new Date(q.ends_at) - Date.now());

      const contrib = document.getElementById('modal-quest-contributions');
      contrib.innerHTML = '';
      Object.entries(q.contributions || {}).forEach(([k,v]) => {
        const li = document.createElement('li');
        li.textContent = `${k.charAt(0).toUpperCase()+k.slice(1)}: ${v.current} / ${v.required}`;
        contrib.appendChild(li);
      });
      if (!contrib.children.length) contrib.innerHTML = '<li>No contributions listed.</li>';

      const rewards = document.getElementById('modal-quest-rewards');
      rewards.innerHTML = '';
      Object.entries(q.rewards || {}).forEach(([k,v]) => {
        const li = document.createElement('li');
        li.textContent = `${k}: ${v}`;
        rewards.appendChild(li);
      });
      if (!rewards.children.length) rewards.innerHTML = '<li>No rewards listed.</li>';

      modalEl.classList.add('visible');
    });
}

/** Format ms to HH:MM:SS */
function formatDuration(ms) {
  if (!ms || ms < 0) return '0s';
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  return `${h}h ${m}m ${secs}s`;
}

// Update countdowns every second
function initCountdowns() {
  document.querySelectorAll('[data-end-time]').forEach(el => {
    const update = () => {
      const diff = new Date(el.dataset.endTime) - Date.now();
      el.textContent = formatDuration(diff);
      if (diff > 0) requestAnimationFrame(update);
    };
    update();
  });
}

// Initial load
document.addEventListener('DOMContentLoaded', () => loadQuests('active'));
