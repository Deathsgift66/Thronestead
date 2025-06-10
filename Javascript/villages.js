import { supabase } from './supabaseClient.js';

let eventSource;

document.addEventListener('DOMContentLoaded', async () => {
  await loadVillages();
  setupRealtime();
  const form = document.getElementById('create-village-form');
  if (form) {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      await createVillage();
    });
  }
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
    renderVillages(villages);
  } catch (err) {
    console.error('❌ Error loading villages:', err);
    listEl.innerHTML = '<li>Failed to load villages.</li>';
  }
}

function renderVillages(villages) {
  const listEl = document.getElementById('village-list');
  listEl.innerHTML = '';
  if (!villages || villages.length === 0) {
    listEl.innerHTML = '<li>No villages found.</li>';
    return;
  }
  villages.forEach(v => {
    const li = document.createElement('li');
    li.innerHTML = `
      <span class="village-name">${escapeHTML(v.village_name)}</span>
      <span>${escapeHTML(v.village_type)}</span>
      <span>${v.population} peasants</span>
      <span>Buildings: ${v.building_count}</span>
    `;
    listEl.appendChild(li);
  });
}

function setupRealtime() {
  try {
    eventSource = new EventSource('/api/kingdom/villages/stream');
    eventSource.onmessage = ev => {
      const villages = JSON.parse(ev.data);
      renderVillages(villages);
    };
  } catch (err) {
    console.error('SSE connection failed', err);
  }
  window.addEventListener('beforeunload', () => {
    if (eventSource) eventSource.close();
  });
}

async function createVillage() {
  const nameInput = document.getElementById('village-name');
  const typeSelect = document.getElementById('village-type');
  const name = nameInput.value.trim();
  const type = typeSelect.value;
  if (!name) return;
  try {
    const { data: { user } } = await supabase.auth.getUser();
    await fetch('/api/kingdom/villages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': user.id
      },
      body: JSON.stringify({ village_name: name, village_type: type })
    });
    nameInput.value = '';
  } catch (err) {
    console.error('Error creating village', err);
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
