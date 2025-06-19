// Project Name: Thronestead©
// File Name: edit_kingdom.js
// Updated for simplified API usage
import { showToast } from './utils.js';

// ------------------------------
// Load Current Kingdom Data
// ------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('/api/kingdom/profile');
    if (!res.ok) throw new Error('Failed to load kingdom');
    const data = await res.json();

    if (data.on_vacation) {
      document.getElementById('vacation-warning').classList.remove('hidden');
      document.getElementById('kingdom-form').style.display = 'none';
      return;
    }

    document.getElementById('kingdom_name').value = data.kingdom_name || '';
    document.getElementById('ruler_name').value = data.ruler_name || '';
    document.getElementById('ruler_title').value = data.ruler_title || '';
    document.getElementById('motto').value = data.motto || '';
    document.getElementById('description').value = data.description || '';
    document.getElementById('religion').value = data.religion || '';
    document.getElementById('region').value = data.region || '';
    document.getElementById('banner_url').value = data.banner_url || '';
    document.getElementById('emblem_url').value = data.emblem_url || '';
    document.getElementById('banner-preview').src =
      data.banner_url || '/Assets/profile_background.png';
    document.getElementById('emblem-preview').src =
      data.emblem_url || '/Assets/icon-scroll.svg';
  } catch (err) {
    console.error(err);
    showToast('Failed to load kingdom');
  }
});

// ------------------------------
// Submit Form to API
// ------------------------------
document.getElementById('kingdom-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    kingdom_name: document.getElementById('kingdom_name').value,
    ruler_name: document.getElementById('ruler_name').value,
    ruler_title: document.getElementById('ruler_title').value,
    motto: document.getElementById('motto').value,
    description: document.getElementById('description').value,
    religion: document.getElementById('religion').value,
    region: document.getElementById('region').value,
    banner_url: document.getElementById('banner_url').value,
    emblem_url: document.getElementById('emblem_url').value
  };

  try {
    const res = await fetch('/api/kingdom/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      showToast('✅ Kingdom updated successfully!');
    } else {
      const { error } = await res.json().catch(() => ({}));
      showToast(`❌ Error: ${error || 'Update failed.'}`);
    }
  } catch (err) {
    console.error(err);
    showToast('❌ Update failed.');
  }
});

// ------------------------------
// Live Preview Handlers
// ------------------------------
document.getElementById('banner_url').addEventListener('input', (e) => {
  document.getElementById('banner-preview').src =
    e.target.value || '/Assets/profile_background.png';
});

document.getElementById('emblem_url').addEventListener('input', (e) => {
  document.getElementById('emblem-preview').src =
    e.target.value || '/Assets/icon-scroll.svg';
});
