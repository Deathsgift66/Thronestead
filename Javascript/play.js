/*
  Project Name: Kingmakers Rise Frontend
  File Name: play.js (enhanced)
  Description: Full onboarding flow with avatar, region, and announcement loading.
  Author: Deathsgift66 + ChatGPT, June 13, 2025
*/

import { supabase } from './supabaseClient.js';

let currentUser = null;
let authToken = '';
let vipLevel = 0;
let selectedAvatar = '';
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

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return redirectTo('login.html');

  currentUser = session.user;
  authToken = session.access_token;

  const { data: profile, error } = await supabase
    .from('users')
    .select('setup_complete, display_name, kingdom_id, kingdom_name')
    .eq('user_id', currentUser.id)
    .maybeSingle();

  if (profile?.setup_complete) return redirectTo('overview.html');

  const displayName = profile?.display_name || profile?.kingdom_name || currentUser.user_metadata.display_name;
  document.getElementById('greeting').textContent = `Welcome, ${escapeHTML(displayName)}!`;

  const nameInput = document.getElementById('kingdom-name-input');
  if (nameInput) {
    nameInput.value = displayName;
    nameInput.readOnly = true;
  }

  selectedAvatar = avatarList[0];
  await loadVIPStatus();
  await loadRegions();
  await loadAnnouncements();
  renderAvatarOptions();
  bindUIEvents();
});

function redirectTo(url) {
  window.location.href = url;
}

function bindUIEvents() {
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
      await postJSON('/api/kingdom/create', {
        kingdom_name: kingdomName,
        ruler_title: rulerTitle,
        village_name: villageName,
        region,
        banner_url: bannerUrl,
        emblem_url: emblemUrl
      });

      await postJSON('/api/account/update', {
        display_name: kingdomName,
        profile_picture_url: selectedAvatar
      });

      showToast('Kingdom created successfully!');
      setTimeout(() => redirectTo('overview.html'), 1200);

    } catch (err) {
      console.error('❌ Kingdom creation error:', err);
      showToast('Failed to create kingdom.');
      createBtn.disabled = false;
    }
  });

  const customAvatar = document.getElementById('custom-avatar-url');
  const avatarPreview = document.getElementById('avatar-preview');
  if (customAvatar && avatarPreview) {
    customAvatar.addEventListener('input', () => {
      selectedAvatar = customAvatar.value.trim() || avatarList[0];
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

function showToast(message) {
  let el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast';
    el.className = 'toast-notification';
    document.body.appendChild(el);
  }
  el.textContent = message;
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

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': currentUser.id,
      Authorization: `Bearer ${authToken}`
    },
    body: JSON.stringify(body)
  });
  const contentType = res.headers.get('content-type') || '';
  if (!res.ok || !contentType.includes('application/json')) {
    const text = await res.text();
    throw new Error(`Failed: ${res.status}, ${text}`);
  }
  return res.json();
}

async function loadVIPStatus() {
  try {
    const res = await fetch('/api/kingdom/vip_status', {
      headers: { 'X-User-ID': currentUser.id }
    });
    if (!res.ok) return;
    const data = await res.json();
    vipLevel = data.vip_level || 0;
  } catch (err) {
    console.warn('Could not load VIP status.');
  }
}

async function loadRegions() {
  const regionEl = document.getElementById('region-select');
  const infoEl = document.getElementById('region-info');
  if (!regionEl || !infoEl) return;

  try {
    const res = await fetch('/api/kingdom/regions');
    const regions = await res.json();
    regionEl.innerHTML = '<option value="">Select Region</option>';

    regions.forEach(region => {
      regionMap[region.region_code] = region;
      const opt = document.createElement('option');
      opt.value = region.region_code;
      opt.textContent = region.region_name;
      regionEl.appendChild(opt);
    });

    regionEl.addEventListener('change', () => {
      const selected = regionMap[regionEl.value];
      if (!selected) return;
      let html = selected.description ? `<p>${escapeHTML(selected.description)}</p>` : '';
      if (selected.resource_bonus) {
        html += '<h4>Resource Bonuses</h4><ul>' +
          Object.entries(selected.resource_bonus).map(([k, v]) =>
            `<li>${escapeHTML(k)}: ${v > 0 ? '+' : ''}${v}%</li>`).join('') + '</ul>';
      }
      if (selected.troop_bonus) {
        html += '<h4>Troop Bonuses</h4><ul>' +
          Object.entries(selected.troop_bonus).map(([k, v]) =>
            `<li>${escapeHTML(k)}: ${v > 0 ? '+' : ''}${v}%</li>`).join('') + '</ul>';
      }
      infoEl.innerHTML = html;
    });
  } catch (err) {
    regionEl.innerHTML = '<option value="">Failed to load regions</option>';
  }
}

async function loadAnnouncements() {
  const el = document.getElementById('announcements');
  if (!el) return;

  try {
    const res = await fetch('/api/login/announcements');
    const announcements = await res.json();
    el.innerHTML = announcements.map(a =>
      `<div class="announcement"><h4>${escapeHTML(a.title)}</h4><p>${escapeHTML(a.content)}</p></div>`
    ).join('');
  } catch (err) {
    el.innerHTML = '<p>Error loading announcements.</p>';
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
  container.querySelector('.avatar-option')?.classList.add('selected');
  if (vipLevel > 0 && custom) custom.classList.remove('hidden');
}
