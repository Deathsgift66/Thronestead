// Project Name: Thronestead©
// File Name: admin_emergency.js
// Version 7.01.2025.08.00
// Developer: Codex (KISS Optimized)

import { authFetch, authJsonFetch } from './utils.js';

// 🔁 Unified POST helper
async function postAction(url, payload) {
  const res = await authFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
}

// 📦 Load Backups
async function loadBackups() {
  const list = document.getElementById('backup-list');
  if (!list) return;
  list.innerHTML = '<li>Loading...</li>';
  try {
    const data = await authJsonFetch('/api/admin/emergency/backups');
    list.innerHTML = '';
    (data.queues || []).forEach(queue => {
      const li = document.createElement('li');
      li.textContent = queue;
      list.appendChild(li);
    });
  } catch (err) {
    console.error('❌ Failed to load backups:', err);
    list.innerHTML = '<li>Error loading queues</li>';
  }
}

// 🚨 Action Map
const actions = {
  'reprocess-tick-btn': {
    inputs: ['tick-war-id'],
    endpoint: '/api/admin/emergency/reprocess_tick',
    payload: ([warId]) => ({ war_id: Number(warId) }),
    success: 'Tick reprocessed'
  },
  'recalc-res-btn': {
    inputs: ['recalc-kingdom-id'],
    endpoint: '/api/admin/emergency/recalculate_resources',
    payload: ([kingdomId]) => ({ kingdom_id: Number(kingdomId) }),
    success: 'Resources recalculated'
  },
  'rollback-quest-btn': {
    inputs: ['quest-alliance-id', 'quest-code'],
    endpoint: '/api/admin/emergency/rollback_quest',
    payload: ([aid, code]) => ({ alliance_id: Number(aid), quest_code: code }),
    success: 'Quest rolled back'
  },
  'load-backups-btn': {
    action: loadBackups
  }
};

// 🧩 DOM Ready Handler
document.addEventListener('DOMContentLoaded', () => {
  Object.entries(actions).forEach(([btnId, config]) => {
    const btn = document.getElementById(btnId);
    if (!btn) return;

    btn.addEventListener('click', async () => {
      if (typeof config.action === 'function') return config.action();

      const values = config.inputs.map(id => document.getElementById(id)?.value.trim());
      if (values.some(v => !v)) return alert('⚠️ All fields required');

      try {
        await postAction(config.endpoint, config.payload(values));
        alert(`✅ ${config.success}`);
      } catch (err) {
        console.error(`❌ ${config.endpoint} failed:`, err);
        alert(`❌ ${err.message}`);
      }
    });
  });
});
