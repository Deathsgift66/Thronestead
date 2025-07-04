// Project Name: Thronestead©
// File Name: play.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML, showToast, fragmentFrom, jsonFetch, openModal, closeModal } from './utils.js';
import { containsBannedContent } from './content_filter.js';

let currentUser = null;
let authToken = '';
let vipLevel = 0;
let selectedAvatar = '';
const regionMap = {};
const avatarList = [
  '/Assets/avatars/Default_avatar_english_king.png',
  '/Assets/avatars/Default_avatar_english_queen.png',
  '/Assets/avatars/Default_avatar_slavic_king.png',
  '/Assets/avatars/Default_avatar_slavic_queen.png',
  '/Assets/avatars/Default_avatar_sultan.png',
  '/Assets/avatars/default_avatar_emperor.png',
  '/Assets/avatars/default_avatar_empress.png',
  '/Assets/avatars/default_avatar_indian_king.png',
  '/Assets/avatars/default_avatar_indian_queen.png',
  '/Assets/avatars/default_avatar_nubian_king.png',
  '/Assets/avatars/default_avatar_nubian_queen.png'
];

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return redirectTo('login.html');

  currentUser = session.user;
  authToken = session.access_token;

  const { data: profile } = await supabase
    .from('users')
    .select('setup_complete, display_name, kingdom_id, kingdom_name')
    .eq('user_id', currentUser.id)
    .maybeSingle();

  if (profile?.setup_complete) return redirectTo('overview.html');

  const displayName = profile?.display_name || profile?.kingdom_name || currentUser.user_metadata.display_name;
  document.getElementById('greeting').textContent = `Welcome, ${escapeHTML(displayName)}!`;

  const nameInput = document.getElementById('kingdom-name-input');
  if (nameInput) nameInput.readOnly = true;

  selectedAvatar = avatarList[0];
  await loadVIPStatus();
  await loadRegions();
  await loadAnnouncements();
  renderAvatarOptions();
  bindUIEvents();
  openModal('name-modal');
});

function redirectTo(url) {
  window.location.href = url;
}

function bindUIEvents() {
  const nextName = document.getElementById('step1-next');
  const nameModalInput = document.getElementById('kingdom-name-modal-input');
  nextName?.addEventListener('click', () => {
    const val = nameModalInput?.value.trim();
    if (!val || val.length < 3) return showToast('Kingdom name must be at least 3 characters.');
    if (containsBannedContent(val)) return showToast('Inappropriate names are not allowed.');
    const mainInput = document.getElementById('kingdom-name-input');
    if (mainInput) {
      mainInput.value = val;
      mainInput.readOnly = true;
    }
    closeModal('name-modal');
    openModal('region-modal');
  });

  const nextRegion = document.getElementById('step2-next');
  const regionModalSelect = document.getElementById('region-modal-select');
  nextRegion?.addEventListener('click', () => {
    const region = regionModalSelect?.value;
    if (!region) return showToast('Please select a region.');
    const mainSelect = document.getElementById('region-select');
    if (mainSelect) {
      mainSelect.value = region;
      mainSelect.dispatchEvent(new Event('change'));
    }
    closeModal('region-modal');
  });

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
      await postJSON('/api/onboarding/kingdom', {
        kingdom_name: kingdomName,
        region
      });
      await postJSON('/api/onboarding/village', { village_name: villageName });
      await postJSON('/api/onboarding/resources');
      await postJSON('/api/onboarding/troop_slots');
      await postJSON('/api/onboarding/noble', { noble_name: 'Founding Noble' });
      await postJSON('/api/onboarding/knight', { knight_name: 'First Knight' });
      await postJSON('/api/onboarding/title');
      await postJSON('/api/onboarding/complete');

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
  if (containsBannedContent(name) || containsBannedContent(village)) {
    return showToast('Inappropriate names are not allowed.');
  }
  if (!region) return showToast('Please select a region.');
  if (!village || village.length < 3) return showToast('Village name must be at least 3 characters.');
  return true;
}


/**
 * POST a JSON payload using the shared `jsonFetch` helper.
 * @param {string} url  Endpoint URL
 * @param {object} body Body object to send
 */
async function postJSON(url, body) {
  return jsonFetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': currentUser.id,
      Authorization: `Bearer ${authToken}`
    },
    body: JSON.stringify(body)
  });
}

async function loadVIPStatus() {
  try {
    const data = await jsonFetch('/api/kingdom/vip_status', {
      headers: { 'X-User-ID': currentUser.id }
    });
    vipLevel = data.vip_level || 0;
  } catch {
    console.warn('Could not load VIP status.');
  }
}

async function loadRegions() {
  const regionEl = document.getElementById('region-select');
  const modalSelect = document.getElementById('region-modal-select');
  const infoEl = document.getElementById('region-info');
  const modalInfo = document.getElementById('region-modal-info');
  if (!regionEl || !infoEl) return;

  try {
    const regions = await jsonFetch('/api/kingdom/regions');
    regionEl.innerHTML = '<option value="">Select Region</option>';
    if (modalSelect) modalSelect.innerHTML = '<option value="">Select Region</option>';

    regions.forEach(region => {
      regionMap[region.region_code] = region;
      const opt = document.createElement('option');
      opt.value = region.region_code;
      opt.textContent = region.region_name;
      regionEl.appendChild(opt.cloneNode(true));
      if (modalSelect) modalSelect.appendChild(opt);
    });

    const updateInfo = (code, target) => {
      const selected = regionMap[code];
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
      target.innerHTML = html;
    };

    regionEl.addEventListener('change', () => updateInfo(regionEl.value, infoEl));
    if (modalSelect && modalInfo) {
      modalSelect.addEventListener('change', () => updateInfo(modalSelect.value, modalInfo));
    }
  } catch {
    regionEl.innerHTML = '<option value="">Failed to load regions</option>';
  }
}

async function loadAnnouncements() {
  const el = document.getElementById('announcements');
  if (!el) return;

  try {
    const { announcements } = await jsonFetch('/api/login/announcements');
    el.innerHTML = announcements.map(a =>
      `<div class="announcement"><h4>${escapeHTML(a.title)}</h4><p>${escapeHTML(a.content)}</p></div>`
    ).join('');
  } catch {
    el.innerHTML = '<p>Error loading announcements.</p>';
  }
}

function renderAvatarOptions() {
  const container = document.getElementById('avatar-options');
  const preview = document.getElementById('avatar-preview');
  const custom = document.getElementById('custom-avatar-container');
  if (!container || !preview) return;

  container.innerHTML = '';
  const frag = fragmentFrom(avatarList, src => {
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
    return img;
  });
  container.appendChild(frag);

  preview.src = selectedAvatar;
  container.querySelector('.avatar-option')?.classList.add('selected');
  if (vipLevel > 0 && custom) custom.classList.remove('hidden');
}
