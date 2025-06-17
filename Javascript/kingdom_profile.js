// Project Name: Thronestead©
// File Name: kingdom_profile.js
// Version 6.14.2025.21.12
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

let targetKingdomId = null;
let currentKingdomId = null;

document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  targetKingdomId = parseInt(urlParams.get('kingdom_id'), 10);
  if (!targetKingdomId) {
    document.getElementById('profile-container').innerHTML = '<p>Invalid kingdom.</p>';
    return;
  }

  await loadCurrentKingdomId();
  await loadProfile();
  setupSpyControls();
});

async function loadCurrentKingdomId() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;
    const res = await fetch('/api/profile/overview', {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'X-User-ID': session.user.id
      }
    });
    const data = await res.json();
    currentKingdomId = data.user?.kingdom_id || null;
  } catch (err) {
    console.warn('Failed to load current kingdom id', err);
  }
}

async function loadProfile() {
  const kNameEl = document.getElementById('kingdom-name');
  const mottoEl = document.getElementById('kingdom-motto');
  const avatarEl = document.getElementById('profile-picture');
  const rulerEl = document.getElementById('ruler-name');
  const prestigeEl = document.getElementById('prestige');

  kNameEl.textContent = 'Loading...';

  try {
    const res = await fetch(`/api/kingdoms/public/${targetKingdomId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to load');

    kNameEl.textContent = data.kingdom_name || 'Unknown Kingdom';
    mottoEl.textContent = data.motto || '';
    rulerEl.textContent = data.ruler_name || '';
    avatarEl.src = data.profile_picture_url || 'Assets/avatars/default_avatar_emperor.png';
    prestigeEl.textContent = data.prestige ? `Prestige: ${data.prestige}` : '';

    if (!data.is_on_vacation && currentKingdomId !== targetKingdomId) {
      document.getElementById('spy-btn').classList.remove('hidden');
    }
  } catch (err) {
    console.error('profile load failed', err);
    kNameEl.textContent = 'Failed to load';
  }
}

function setupSpyControls() {
  const btn = document.getElementById('spy-btn');
  const modal = document.getElementById('spy-modal');
  const closeBtn = document.getElementById('close-spy-modal');

  if (btn) btn.addEventListener('click', () => modal.classList.remove('hidden'));
  if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.add('hidden'));

  document.querySelectorAll('.spy-option').forEach(el => {
    el.addEventListener('click', () => {
      const mission = el.dataset.mission;
      window.location.href = `spies.html?target_id=${targetKingdomId}&mission=${mission}`;
    });
  });
}
