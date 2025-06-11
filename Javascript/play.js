/*
Project Name: Kingmakers Rise Frontend
File Name: play.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let currentUser = null;
let kingdomId = null;
let authToken = '';
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
let vipLevel = 0;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  currentUser = session.user;
  authToken = session.access_token;

  const { data: profile, error } = await supabase
    .from('users')
    .select('setup_complete, kingdom_id, display_name')
    .eq('user_id', currentUser.id)
    .maybeSingle();

  if (error && profile !== null) {
    console.error('❌ Error loading profile:', error);
    showToast('Failed to load profile.');
    return;
  }

  if (profile && profile.setup_complete) {
    window.location.href = 'overview.html';
    return;
  }

  const nameInput = document.getElementById('kingdom-name-input');

  if (profile) {
    kingdomId = profile.kingdom_id;
    document.getElementById('greeting').textContent = `Welcome, ${escapeHTML(profile.display_name)}!`;
    if (nameInput) nameInput.value = profile.display_name;
  } else {
    document.getElementById('greeting').textContent = `Welcome, ${escapeHTML(currentUser.user_metadata.display_name)}!`;
    if (nameInput) nameInput.value = currentUser.user_metadata.display_name;
  }

  if (nameInput) nameInput.readOnly = true;

  await loadVIPStatus();
  await loadRegions();
  await loadAnnouncements();
  renderAvatarOptions();
  bindEvents(profile);
});

function bindEvents(profileExists) {
  const createBtn = document.getElementById('create-kingdom-btn');
  const bannerPreview = document.getElementById('banner-preview');
  const emblemPreview = document.getElementById('emblem-preview');
  const bannerEl = document.getElementById('banner-image-input');
  const emblemEl = document.getElementById('emblem-image-input');
  const customAvatarEl = document.getElementById('custom-avatar-url');

  if (customAvatarEl) {
    customAvatarEl.addEventListener('input', () => {
      selectedAvatar = customAvatarEl.value.trim() || avatarList[0];
      document.getElementById('avatar-preview').src = selectedAvatar;
    });
  }

  if (bannerEl && bannerPreview) {
    bannerEl.addEventListener('input', () => {
      bannerPreview.src = bannerEl.value.trim();
    });
  }
  if (emblemEl && emblemPreview) {
    emblemEl.addEventListener('input', () => {
      emblemPreview.src = emblemEl.value.trim();
    });
  }

  createBtn.addEventListener('click', async () => {
    const kNameEl = document.getElementById('kingdom-name-input');
    const titleEl = document.getElementById('ruler-title-input');
    const regionEl = document.getElementById('region-select');
    const villageEl = document.getElementById('village-name-input');
    const bannerEl = document.getElementById('banner-image-input');
    const emblemEl = document.getElementById('emblem-image-input');
    if (bannerEl && bannerPreview) {
      bannerPreview.src = bannerEl.value;
    }
    if (emblemEl && emblemPreview) {
      emblemPreview.src = emblemEl.value;
    }
    const mottoEl = document.getElementById('motto-input');

    const kingdomName = kNameEl.value.trim();
    const rulerTitle = titleEl.value.trim();
    const region = regionEl.value;
    const villageName = villageEl.value.trim();
    const bannerImage = bannerEl.value.trim();
    const emblemImage = emblemEl.value.trim();
    const motto = mottoEl.value.trim();

    if (kingdomName.length < 3) {
      showToast('Kingdom name must be at least 3 characters.');
      return;
    }
    if (!region) {
      showToast('Please select a region.');
      return;
    }
    if (villageName.length < 3) {
      showToast('Village name must be at least 3 characters.');
      return;
    }

    createBtn.disabled = true;

    try {
      const res = await fetch('/api/kingdom/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': currentUser.id,
          Authorization: `Bearer ${authToken}`
        },
        body: JSON.stringify({
          kingdom_name: kingdomName,
          ruler_title: rulerTitle || null,
          village_name: villageName,
          region,
          banner_image: bannerImage || null,
          emblem_image: emblemImage || null,
          motto: motto || null
        })
      });

      if (!res.ok) throw new Error('Request failed');

      await fetch('/api/account/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': currentUser.id,
          Authorization: `Bearer ${authToken}`
        },
        body: JSON.stringify({
          display_name: kingdomName,
          profile_picture_url: selectedAvatar
        })
      });

      showToast('Kingdom created!');
      setTimeout(() => {
        window.location.href = 'overview.html';
      }, 1500);
    } catch (err) {
      console.error('❌ Error creating kingdom:', err);
      showToast('Failed to create kingdom.');
      createBtn.disabled = false;
    }
  });
}

function showToast(msg) {
  let toastEl = document.getElementById('toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.id = 'toast';
    toastEl.className = 'toast-notification';
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  setTimeout(() => toastEl.classList.remove('show'), 3000);
}

function escapeHTML(str) {
  return str?.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function loadRegions() {
  const regionEl = document.getElementById('region-select');
  const infoEl = document.getElementById('region-info');
  if (!regionEl) return;

  const { data: regions, error } = await supabase
    .from('region_catalogue')
    .select('*');

  if (error) {
    console.error('Failed to load regions', error);
    regionEl.innerHTML = '<option value="">Failed to load</option>';
    return;
  }

  regionEl.innerHTML = '<option value="">Select Region</option>';
  regions.forEach(r => {
    regionMap[r.region_code] = r;
    const opt = document.createElement('option');
    opt.value = r.region_code;
    opt.textContent = r.region_name || r.region_code;
    regionEl.appendChild(opt);
  });

  regionEl.addEventListener('change', () => {
    const code = regionEl.value;
    infoEl.innerHTML = '';
    if (!code) return;
    const r = regionMap[code];
    if (!r) return;
    let html = '';
    if (r.description) html += `<p>${escapeHTML(r.description)}</p>`;
    if (r.resource_bonus && Object.keys(r.resource_bonus).length > 0) {
      html += '<ul>';
      for (const [res, amt] of Object.entries(r.resource_bonus)) {
        html += `<li>${escapeHTML(res)}: ${amt > 0 ? '+' : ''}${amt}%</li>`;
      }
      html += '</ul>';
    }
    if (r.troop_bonus && Object.keys(r.troop_bonus).length > 0) {
      html += '<ul>';
      for (const [stat, val] of Object.entries(r.troop_bonus)) {
        html += `<li>${escapeHTML(stat)}: ${val > 0 ? '+' : ''}${val}%</li>`;
      }
      html += '</ul>';
    }
    infoEl.innerHTML = html;
  });
}

async function loadAnnouncements() {
  const container = document.getElementById('announcements');
  if (!container) return;
  try {
    const res = await fetch('/api/login/announcements');
    if (!res.ok) throw new Error('fetch failed');
    const data = await res.json();
    const items = data.announcements || [];
    container.innerHTML = items
      .map(a => `<div class="announcement"><h4>${escapeHTML(a.title)}</h4><p>${escapeHTML(a.content)}</p></div>`)
      .join('');
  } catch (err) {
    console.error('Failed to load announcements', err);
  }
}

async function loadVIPStatus() {
  try {
    const res = await fetch('/api/kingdom/vip_status', {
      headers: { 'X-User-ID': currentUser.id }
    });
    const data = await res.json();
    vipLevel = data.vip_level || 0;
  } catch (e) {
    vipLevel = 0;
  }
}

function renderAvatarOptions() {
  const container = document.getElementById('avatar-options');
  const customContainer = document.getElementById('custom-avatar-container');
  if (!container) return;
  container.innerHTML = '';
  avatarList.forEach(src => {
    const img = document.createElement('img');
    img.src = src;
    img.alt = 'Avatar Option';
    img.className = 'avatar-option';
    img.addEventListener('click', () => {
      selectedAvatar = src;
      document.querySelectorAll('.avatar-option').forEach(el => el.classList.remove('selected'));
      img.classList.add('selected');
      document.getElementById('avatar-preview').src = src;
    });
    container.appendChild(img);
  });
  document.getElementById('avatar-preview').src = selectedAvatar;
  const first = container.querySelector('.avatar-option');
  if (first) first.classList.add('selected');
  if (vipLevel > 0 && customContainer) {
    customContainer.classList.remove('hidden');
  }
}
