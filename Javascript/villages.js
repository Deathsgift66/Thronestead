import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  await loadVillages();
});

async function loadVillages() {
  const listEl = document.getElementById('village-list');
  listEl.innerHTML = '<li>Loading villages...</li>';

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/kingdom/villages', {
      headers: { 'X-User-ID': user.id }
    });
    const { villages } = await res.json();

    listEl.innerHTML = '';

    if (!villages || villages.length === 0) {
      listEl.innerHTML = '<li>No villages found.</li>';
      return;
    }
    villages.forEach(village => {
      const li = document.createElement('li');
      li.innerHTML = `
        <strong>${escapeHTML(village.village_name)}</strong> - ${escapeHTML(village.village_type)}
        <em>${new Date(village.created_at).toLocaleDateString()}</em>
        <span>Buildings: ${village.buildings.length}</span>
      `;
      listEl.appendChild(li);
    });
  } catch (err) {
    console.error('❌ Error loading villages:', err);
    listEl.innerHTML = '<li>Failed to load villages.</li>';
  }
}

function escapeHTML(str) {
  return str?.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
