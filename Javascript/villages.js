// Project Name: Thronestead©
// File Name: villages.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Village Management with Server-Sent Events & Real-Time Updates

import { supabase } from '../supabaseClient.js';
import { escapeHTML, showToast, fragmentFrom } from './utils.js';
import { getEnvVar } from './env.js';
const API_BASE_URL = getEnvVar('API_BASE_URL');

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

// Load villages from API and render them
async function loadVillages() {
  const listEl = document.getElementById('village-list');
  listEl.innerHTML = '<li>Loading villages...</li>';

  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session || !session.user) throw new Error('No session');
    const user = session.user;
    const res = await fetch(`${API_BASE_URL}/api/kingdom/villages`, {
      headers: { 'X-User-ID': user.id }
    });
    if (!res.ok) throw new Error('Failed to load villages');
    const { villages } = await res.json();
    renderVillages(villages);
  } catch (err) {
    console.error('❌ Error loading villages:', err);
    listEl.innerHTML = '<li>Failed to load villages.</li>';
  }
}

// Render the village list with safe escaping
function renderVillages(villages) {
  const listEl = document.getElementById('village-list');
  listEl.innerHTML = '';
  if (!villages || villages.length === 0) {
    listEl.innerHTML = '<li>No villages found.</li>';
    return;
  }

  const frag = fragmentFrom(villages, v => {
    const li = document.createElement('li');
    li.className = 'village-item';
    li.innerHTML = `
      <span class="village-name">${escapeHTML(v.village_name)}</span>
      <span class="village-type">${escapeHTML(v.village_type)}</span>
      <span class="village-buildings">Buildings: ${v.building_count.toLocaleString()}</span>
    `;
    return li;
  });

  listEl.appendChild(frag);
}

// Setup Server-Sent Events connection for real-time updates
function setupRealtime() {
  try {
    eventSource = new EventSource(`${API_BASE_URL}/api/kingdom/villages/stream`);
    eventSource.onmessage = ev => {
      try {
        const villages = JSON.parse(ev.data);
        renderVillages(villages);
      } catch (e) {
        console.error('Failed to parse SSE data', e);
      }
    };
    eventSource.onerror = e => {
      console.warn('🔁 SSE connection error. Will attempt reconnect...');
      showToast('Real-time updates lost. Reload to reconnect.');
      eventSource.close();
      setTimeout(() => {
        setupRealtime();
      }, 5000);
    };
  } catch (err) {
    console.error('SSE initialization failed', err);
  }
  window.addEventListener('beforeunload', () => {
    if (eventSource) eventSource.close();
  });
}

// Create a new village via API call
async function createVillage() {
  const nameInput = document.getElementById('village-name');
  const typeSelect = document.getElementById('village-type');
  const name = nameInput.value.trim();
  const type = typeSelect.value;
  if (!name) {
    showToast("Village name cannot be empty.");
    return;
  }
  if (name.length < 3 || name.length > 40) {
    showToast("Village name must be 3–40 characters.");
    return;
  }
  if (!/^[A-Za-z0-9\s\-\'’]+$/.test(name)) {
    showToast("Name contains invalid characters.");
    return;
  }
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session || !session.user) throw new Error('No session');
    const user = session.user;
    const res = await fetch(`${API_BASE_URL}/api/kingdom/villages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': user.id
      },
      body: JSON.stringify({ village_name: name, village_type: type })
    });
    if (!res.ok) {
      let errorMessage = 'Failed to create village';
      try {
        const errorData = await res.json();
        if (errorData?.detail) errorMessage = errorData.detail;
      } catch {}
      throw new Error(errorMessage);
    }
    nameInput.value = '';
    showToast("Village created successfully!");
  } catch (err) {
    console.error('Error creating village', err);
    showToast("Failed to create village.");
  }
}

