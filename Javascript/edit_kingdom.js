// Project Name: Thronestead©
// File Name: edit_kingdom.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from './supabaseClient.js';
import { showToast } from './core_utils.js';
import { authHeaders } from './auth.js';
import { setupPreview } from './account_previews.js';

document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('kingdom-form');
  const bannerPreview = document.getElementById('banner-preview');
  const emblemPreview = document.getElementById('emblem-preview');

  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  await loadRegions();

  const res = await fetch('/api/kingdom/profile', {
    headers: await authHeaders()
  });
  const kingdom = await res.json();
  populateForm(kingdom);

  setupPreview('banner_url', 'banner-preview', 'Assets/profile_background.png');
  setupPreview('emblem_url', 'emblem-preview', 'Assets/icon-scroll.svg');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (!validateName()) return;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
      const save = await fetch('/api/kingdom/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(await authHeaders())
        },
        body: JSON.stringify(payload)
      });

      const result = await save.json();
      if (!save.ok) throw new Error(result.detail || 'Update failed');

      showToast('✅ Kingdom updated');
    } catch (err) {
      console.error(err);
      showToast('❌ Failed to update kingdom');
    }
  });
});

function validateName() {
  const el = document.getElementById('kingdom_name');
  const name = el.value.trim();
  const valid = /^[A-Za-z0-9 '\-,]{3,32}$/.test(name);
  if (!valid) {
    showToast('❌ Kingdom Name must be 3–32 letters/numbers');
    el.focus();
  }
  return valid;
}

async function loadRegions() {
  const select = document.getElementById('region');
  if (!select) return;
  try {
    const res = await fetch('/api/kingdom/regions');
    const regions = await res.json();
    select.innerHTML = '<option value="">Select Region</option>';
    regions.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.region_code || r.region_name;
      opt.textContent = r.region_name;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error('Failed to load regions:', err);
    select.innerHTML = '<option value="">Failed to load regions</option>';
  }
}

function populateForm(data) {
  for (const key in data) {
    const el = document.getElementById(key);
    if (el && typeof data[key] === 'string') el.value = data[key];
  }

  const region = document.getElementById('region');
  if (region && data.region) {
    const option = new Option(data.region, data.region, true, true);
    region.appendChild(option);
  }

  if (data.vacation_mode) {
    document.getElementById('vacation-warning')?.classList.remove('hidden');
    const form = document.getElementById('kingdom-form');
    form.classList.add('disabled');
    form.querySelectorAll('input, textarea, select, button').forEach(el => {
      el.disabled = true;
    });
  }
}

