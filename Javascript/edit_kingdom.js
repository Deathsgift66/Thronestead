// Project Name: Thronestead©
// File Name: edit_kingdom.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { showToast, isValidURL, setValue, getValue } from './utils.js';

let userId = null;
let authToken = '';

// ------------------------------
// DOM Ready Init
// ------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const sessionRes = await supabase.auth.getSession();
    const session = sessionRes.data.session;
    if (!session) return redirectToLogin();

    userId = session.user.id;
    authToken = session.access_token;

    await loadRegions();
    await loadKingdomData();

    bindInputPreview();
    bindFormSubmission();
  } catch (err) {
    console.error('Initialization error:', err);
    showToast('Failed to initialize page.');
  }
});

// ------------------------------
// Load Available Regions
// ------------------------------
async function loadRegions() {
  const sel = document.getElementById('region');
  sel.innerHTML = '<option>Loading...</option>';
  const { data, error } = await supabase.from('region_catalogue').select('*');
  if (error || !data) {
    sel.innerHTML = '<option value="">Failed to load regions</option>';
    return;
  }

  sel.innerHTML = '<option value="">Select Region</option>';
  data.forEach(region => {
    const opt = document.createElement('option');
    opt.value = region.region_code;
    opt.textContent = region.region_name || region.region_code;
    sel.appendChild(opt);
  });
}

// ------------------------------
// Load Current Kingdom Data
// ------------------------------
async function loadKingdomData() {
  const { data, error } = await supabase
    .from('kingdoms')
    .select(`
      ruler_name, ruler_title, kingdom_name, motto, description,
      region, banner_url, emblem_url, is_on_vacation,
      kingdom_religion(religion_name)
    `)
    .eq('owner_id', userId)
    .single();

  if (error || !data) return showToast('Failed to load kingdom');

  setValue('ruler_name', data.ruler_name);
  setValue('ruler_title', data.ruler_title);
  setValue('kingdom_name', data.kingdom_name);
  setValue('motto', data.motto);
  setValue('description', data.description);
  setValue('region', data.region);
  setValue('banner_url', data.banner_url);
  setValue('emblem_url', data.emblem_url);
  setValue('religion', data.kingdom_religion?.religion_name);

  if (data.banner_url) setImagePreview('banner-preview', data.banner_url);
  if (data.emblem_url) setImagePreview('emblem-preview', data.emblem_url);

  if (data.is_on_vacation) {
    document.getElementById('vacation-warning')?.classList.remove('hidden');
    document.querySelectorAll('#kingdom-form input, #kingdom-form textarea, #kingdom-form select, #kingdom-form button')
      .forEach(el => el.disabled = true);
  }
}

// ------------------------------
// Form Submission
// ------------------------------
function bindFormSubmission() {
  const form = document.getElementById('kingdom-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      ruler_name: getValue('ruler_name'),
      ruler_title: getValue('ruler_title'),
      kingdom_name: getValue('kingdom_name'),
      motto: getValue('motto', true),
      description: getValue('description', true),
      region: getValue('region', true),
      banner_url: getValue('banner_url', true),
      emblem_url: getValue('emblem_url', true),
      religion_name: getValue('religion', true)
    };

    if (!payload.ruler_name || !payload.ruler_title || !payload.kingdom_name) {
      return showToast('Name and title are required.');
    }

    if (payload.banner_url && !isValidURL(payload.banner_url)) {
      return showToast('Invalid banner URL.');
    }
    if (payload.emblem_url && !isValidURL(payload.emblem_url)) {
      return showToast('Invalid emblem URL.');
    }

    const res = await fetch('/api/kingdom/update', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
        'X-User-ID': userId
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) return showToast('Failed to save changes');
    showToast('Kingdom updated!');
  });
}

// ------------------------------
// Live Banner & Emblem Preview
// ------------------------------
function bindInputPreview() {
  const bannerInput = document.getElementById('banner_url');
  const emblemInput = document.getElementById('emblem_url');

  if (bannerInput) {
    bannerInput.addEventListener('input', e => {
      setImagePreview('banner-preview', e.target.value);
    });
  }

  if (emblemInput) {
    emblemInput.addEventListener('input', e => {
      setImagePreview('emblem-preview', e.target.value);
    });
  }
}

function setImagePreview(id, url) {
  const img = document.getElementById(id);
  if (img && isValidURL(url)) img.src = url;
}

function redirectToLogin() {
  window.location.href = 'login.html';
}
