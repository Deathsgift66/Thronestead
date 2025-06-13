/*
  Project Name: Kingmakers Rise Frontend
  File Name: play.js (rewritten)
  Description: Handles onboarding setup, region/announcement loading, and kingdom creation.
  Author: Rewritten by OpenAI, June 13, 2025
*/

import { supabase } from './supabaseClient.js';

let currentUser = null;
let kingdomId = null;
let authToken = '';
let vipLevel = 0;
const regionMap = {};
const avatarList = [
  'Assets/avatars/Default_avatar_english_king.png',
  'Assets/avatars/Default_avatar_english_queen.png',
  'Assets/avatars/Default_avatar_slavic_king.png',
  'Assets/avatars/Default_avatar_slavic_queen.png',
  'Assets/avatars/Default_avatar_sultan.png',
  'Assets/avatars/default_avatar_emperor.png',
  'Assets/avatars/default_avatar_empress.png',
  'Assets/avatars/default_avatar_indian_king.png',
  'Assets/avatars/default_avatar_indian_queen.png',
  'Assets/avatars/default_avatar_nubian_king.png',
  'Assets/avatars/default_avatar_nubian_queen.png'
];
let selectedAvatar = avatarList[0];

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return redirectTo('login.html');

  currentUser = session.user;
  authToken = session.access_token;

  const { data: profile, error } = await supabase
    .from('users')
    .select('setup_complete, kingdom_id, display_name, kingdom_name')
    .eq('user_id', currentUser.id)
    .maybeSingle();

  if (error) {
    console.error('Profile error:', error);
    showToast('Failed to load profile.');
    return;
  }

  if (profile?.setup_complete) return redirectTo('overview.html');

  kingdomId = profile?.kingdom_id ?? null;
  const displayName = profile?.display_name || profile?.kingdom_name || currentUser.user_metadata.display_name;
  document.getElementById('greeting').textContent = `Welcome, ${escapeHTML(displayName)}!`;

  const nameInput = document.getElementById('kingdom-name-input');
  if (nameInput) {
    nameInput.value = displayName;
    nameInput.readOnly = true;
  }

  await loadVIPStatus();
  await loadRegions();
  await loadAnnouncements();
  renderAvatarOptions();
  bindEvents();
});

function redirectTo(url) {
  window.location.href = url;
}

function bindEvents() {
  const createBtn = document.getElementById('create-kingdom-btn');
  if (!createBtn) return;

  createBtn.addEventListener('click', async () => {
    const kingdomName = document.getElementById('kingdom-name-input')?.value.trim();
    const rulerTitle = document.getElementById('ruler-title-input')?.value.trim() || null;
    const region = document.getElementById('region-select')?.value;
    const villageName = document.getElementById('village-name-input')?.value.trim();
    const bannerUrl = document.getElementById('banner_url')?.value.trim() || null;
    const emblemUrl = document.getElementById('emblem_url')?.value.trim() || null;

    if (!validateInputs(kingdomName, villageName, region)) return;

    createBtn.disabled = true;

    try {
      await safeJSONPost('/api/kingdom/create', {
        kingdom_name: kingdomName,
        ruler_title: rulerTitle,
        village_name: villageName,
        region,
        banner_url: bannerUrl,
        emblem_url: emblemUrl
      });

      await safeJSONPost('/api/account/update', {
        display_name: kingdomName,
        profile_picture_url: selectedAvatar
      });

      showToast('Kingdom created!');
      setTimeout(() => redirectTo('overview.html'), 1500);
    } catch (err) {
      console.error('❌ Error creating kingdom:', err);
      showToast('Failed to create kingdom.');
      createBtn.disabled = false;
    }
  });

  const customAvatarEl = document.getElementById('custom-avatar-url');
  const avatarPreview = document.getElementById('avatar-preview');
  if (customAvatarEl && avatarPreview) {
    customAvatarEl.addEventListener('input', () => {
      selectedAvatar = customAvatarEl.value.trim() || avatarList[0];
      avatarPreview.src = selectedAvatar;
    });
  }

  ['banner_url', 'emblem_url'].forEach(id => {
    const input = document.getElementById(id);
    const preview = document.getElementById(`${id.replace('_url', '')}-preview`);
    if (input && preview) {
      input.addEventListener('input', () => preview.src = input.value.trim());
    }
  });
}

function validateInputs(name, village, region) {
  if (!name || name.length < 3) return showToast('Kingdom name must be at least 3 characters.');
  if (!region) return showToast('Please select a region.');
  if (!village || village.length < 3) return showToast('Village name must be at least 3 characters.');
  return true;
}

function showToast(msg) {
  let el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast';
    el.className = 'toast-notification';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 3000);
}

function escapeHTML(str) {
  return str?.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function safeJSONGet(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} - ${res.statusText}`);
  const type = res.headers.get('content-type') || '';
  if (!type.includes('application/json')) {
    const text = await res.text();
    throw new Error(`Invalid JSON: ${text.slice(0, 100)}`);
  }
  return res.json();
}

async function safeJSONPost(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': currentUser.id,
      Authorization: `Bearer ${authToken}`
    },
    body: JSON.stringify(data)
  });

  if (!res.ok) throw new Error(`POST failed: ${res.status}`);
  const type = res.headers.get('content-type') || '';
  if (!type.includes('application/json')) {
    const text = await res.text();
    throw new Error(`Invalid JSON in response: ${text}`);
  }

  return res.json();
}

async function loadRegions() {
  const regionEl = document.getElementById('region-select');
  const infoEl = document.getElementById('region-info');
  if (!regionEl || !infoEl) return;

  try {
    const regions = await safeJSONGet('/api/kingdom/regions');
    regionEl.innerHTML = '<option value="">Select Region</option>';

    regions.forEach(region => {
      regionMap[region.region_code] = region;

      const opt = document.createElement('option');
      opt.value = region.region_code;
      opt.textContent = region.region_name;
      regionEl.appendChild(opt);
    });

    regionEl.addEventListener('change', () => {
      const region = regionMap[regionEl.value];
      infoEl.innerHTML = '';
      if (!region) return;

      let html = region.description ? `<p>${escapeHTML(region.description)}</p>` : '';
      if (region.resource_bonus && Object.keys(region.resource_bonus).length) {
        html += '<ul>' + Object.entries(region.resource_bonus)
          .map(([res, amt]) => `<li>${escapeHTML(res)}: ${amt > 0 ? '+' : ''}${amt}%</li>`).join('') + '</ul>';
      }
      if (region.troop_bonus && Object.keys(region.troop_bonus).length) {
        html += '<ul>' + Object.entries(region.troop_bonus)
          .map(([stat, val]) => `<li>${escapeHTML(stat)}: ${val > 0 ? '+' : ''}${val}%</li>`).join('') + '</ul>';
      }
      infoEl.innerHTML = html;
    });
  } catch (err) {
    console.error('Failed to load regions:', err);
    regionEl.innerHTML = '<option value="">Failed to load regions</option>';
  }
}

async function loadAnnouncements() {
  const container = document.getElementById('announcements');
  if (!container) return;
  try {
    const announcements = await safeJSONGet('/api/login/announcements');
    container.innerHTML = announcements.map(a =>
      `<div class="announcement"><h4>${escapeHTML(a.title)}</h4><p>${escapeHTML(a.content)}</p></div>`
    ).join('');
  } catch (err) {
    console.error('Failed to load announcements:', err);
    container.innerHTML = '<p>Error loading announcements.</p>';
  }
}

async function loadVIPStatus() {
  try {
    const data = await fetch('/api/kingdom/vip_status', {
      headers: { 'X-User-ID': currentUser.id }
    });

    if (!data.ok) return;

    const contentType = data.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) return;

    const json = await data.json();
    vipLevel = json.vip_level || 0;
  } catch (err) {
    console.error('VIP status fetch failed:', err);
  }
}

function renderAvatarOptions() {
  const container = document.getElementById('avatar-options');
  const preview = document.getElementById('avatar-preview');
  const custom = document.getElementById('custom-avatar-container');
  if (!container || !preview) return;

  container.innerHTML = '';
  avatarList.forEach(src => {
    const img = document.createElement('img');
    img.src = src;
    img.alt = 'Avatar Option';
    img.className = 'avatar-option';
    img.addEventListener('click', () => {
      selectedAvatar = src;
      document.querySelectorAll('.avatar-option').forEach(i => i.classList.remove('selected'));
      img.classList.add('selected');
      preview.src = src;
    });
    container.appendChild(img);
  });

  preview.src = selectedAvatar;
  const first = container.querySelector('.avatar-option');
  if (first) first.classList.add('selected');
  if (vipLevel > 0 && custom) custom.classList.remove('hidden');
}

