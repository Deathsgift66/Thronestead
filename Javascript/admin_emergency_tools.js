// Project Name: Thronestead©
// File Name: admin_emergency_tools.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import {
  authFetch,
  authJsonFetch,
  escapeHTML,
  showToast,
  openModal,
  closeModal,
  toggleLoading
} from './utils.js';

let pendingAction = null;

// 🔁 Unified POST helper
async function postAction(url, payload) {
  const res = await authFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
}

// 🔍 Apply backup search filter
function applyFilter() {
  const input = document.getElementById('backup-filter');
  const term = input?.value.toLowerCase() || '';
  const list = document.getElementById('backup-list');
  Array.from(list.children).forEach(li => {
    const match = li.dataset.queue?.includes(term);
    li.style.display = match ? '' : 'none';
  });
}

// 📦 Load Backups
async function loadBackups(btn) {
  const list = document.getElementById('backup-list');
  if (!list) return;
  btn?.setAttribute('disabled', 'disabled');
  list.innerHTML = '<li>Loading...</li>';
  toggleLoading(true);
  try {
    const data = await authJsonFetch('/api/admin/emergency/backups');
    list.innerHTML = '';
    (data.queues || []).forEach(queue => {
      const li = document.createElement('li');
      li.dataset.queue = queue.toLowerCase();
      li.textContent = escapeHTML(queue);
      list.appendChild(li);
    });
    const time = document.getElementById('backup-time');
    if (time) time.textContent = `Last loaded: ${new Date().toLocaleString()}`;
    applyFilter();
    showToast('Backups loaded');
  } catch (err) {
    console.error('❌ Failed to load backups:', err);
    list.innerHTML = '<li>Error loading queues</li>';
    showToast('Failed to load backups');
  } finally {
    btn?.removeAttribute('disabled');
    toggleLoading(false);
  }
}

// 🚨 Action Map
const actions = {
  'reprocess-tick-btn': {
    inputs: ['tick-war-id'],
    endpoint: '/api/admin/emergency/reprocess_tick',
    payload: ([warId]) => ({ war_id: Number(warId) }),
    success: 'Tick reprocessed',
    confirm: true
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
    success: 'Quest rolled back',
    confirm: true
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
      const execute = async () => {
        if (typeof config.action === 'function') return config.action(btn);

        const values = config.inputs.map(id => document.getElementById(id)?.value.trim());
        if (values.some(v => !v)) return showToast('⚠️ All fields required');

        btn.disabled = true;
        toggleLoading(true);
        try {
          await postAction(config.endpoint, config.payload(values));
          showToast(`✅ ${config.success}`);
        } catch (err) {
          console.error(`❌ ${config.endpoint} failed:`, err);
          showToast(`❌ ${err.message}`);
        } finally {
          btn.disabled = false;
          toggleLoading(false);
        }
      };

      if (config.confirm) {
        pendingAction = execute;
        openModal('confirm-modal');
      } else {
        execute();
      }
    });
  });

  document.getElementById('backup-filter')?.addEventListener('input', applyFilter);

  const confirmYes = document.getElementById('confirm-yes');
  const confirmNo = document.getElementById('confirm-no');
  confirmYes?.addEventListener('click', () => {
    closeModal('confirm-modal');
    pendingAction?.();
    pendingAction = null;
  });
  confirmNo?.addEventListener('click', () => {
    closeModal('confirm-modal');
    pendingAction = null;
  });
});
