import { authFetch, authJsonFetch } from './utils.js';

async function postAction(url, payload) {
  const res = await authFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
}

async function loadBackups() {
  const list = document.getElementById('backup-list');
  if (!list) return;
  list.innerHTML = '<li>Loading...</li>';
  try {
    const data = await authJsonFetch('/api/admin/emergency/backups');
    list.innerHTML = '';
    data.queues.forEach(q => {
      const li = document.createElement('li');
      li.textContent = q;
      list.appendChild(li);
    });
  } catch (err) {
    console.error(err);
    list.innerHTML = '<li>Error loading queues</li>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('reprocess-tick-btn')?.addEventListener('click', async () => {
    const id = document.getElementById('tick-war-id').value;
    if (!id) return alert('Enter war ID');
    try {
      await postAction('/api/admin/emergency/reprocess_tick', { war_id: Number(id) });
      alert('Tick reprocessed');
    } catch (err) {
      alert(err.message);
    }
  });

  document.getElementById('recalc-res-btn')?.addEventListener('click', async () => {
    const id = document.getElementById('recalc-kingdom-id').value;
    if (!id) return alert('Enter kingdom ID');
    try {
      await postAction('/api/admin/emergency/recalculate_resources', { kingdom_id: Number(id) });
      alert('Resources recalculated');
    } catch (err) {
      alert(err.message);
    }
  });

  document.getElementById('rollback-quest-btn')?.addEventListener('click', async () => {
    const aid = document.getElementById('quest-alliance-id').value;
    const code = document.getElementById('quest-code').value;
    if (!aid || !code) return alert('Enter alliance ID and quest code');
    try {
      await postAction('/api/admin/emergency/rollback_quest', { alliance_id: Number(aid), quest_code: code });
      alert('Quest rolled back');
    } catch (err) {
      alert(err.message);
    }
  });

  document.getElementById('load-backups-btn')?.addEventListener('click', loadBackups);
});
