import { supabase } from './supabaseClient.js';

async function loadUserProfile() {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error('Unauthorized');
  const res = await fetch('/api/account/profile', {
    headers: { 'X-User-ID': user.id }
  });
  if (!res.ok) throw new Error('Failed to load profile');
  const info = await res.json();

  document.getElementById('avatar-preview').src = info.profile_picture_url || '/avatars/default_avatar.png';
  document.getElementById('avatar_url').value = info.profile_picture_url || '';
  document.getElementById('display_name').value = info.display_name || '';
  document.getElementById('motto').value = info.motto || '';
  document.getElementById('profile_bio').value = info.bio || '';
  document.getElementById('email').value = info.email;
  document.getElementById('profile_banner').value = info.profile_banner || '';
  document.getElementById('banner-preview').src = info.profile_banner || '/assets/profile_banners/default.jpg';
  document.getElementById('theme_preference').value = info.theme_preference || 'parchment';
  const vipElement = document.getElementById('vip-status');
  vipElement.innerText = info.vip_level ? `VIP ${info.vip_level}` : 'Not a VIP';
  if (info.founder) vipElement.innerText += ' (Founder)';

  const tbody = document.querySelector('#sessions-table tbody');
  tbody.innerHTML = '';
  info.sessions.forEach((s) => {
    const row = document.createElement('tr');
    row.id = `session-${s.session_id}`;
    row.innerHTML = `<td>${s.device}</td><td>${s.last_seen}</td><td><button class="logout-session" data-id="${s.session_id}">Logout</button></td>`;
    tbody.appendChild(row);
  });
}

async function saveUserSettings() {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error('Unauthorized');
  const payload = {
    display_name: document.getElementById('display_name').value,
    motto: document.getElementById('motto').value,
    bio: document.getElementById('profile_bio').value,
    profile_picture_url: document.getElementById('avatar_url').value,
    theme_preference: document.getElementById('theme_preference').value,
    profile_banner: document.getElementById('profile_banner').value,
  };
  const res = await fetch('/api/account/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to save');
  alert('Settings saved');
}

async function logoutSession(sessionId) {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return;
  await fetch('/api/account/logout-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
    body: JSON.stringify({ session_id: sessionId })
  });
  document.getElementById(`session-${sessionId}`).remove();
}

function uploadAvatar() {
  const url = document.getElementById('avatar_url').value;
  document.getElementById('avatar-preview').src = url || '/avatars/default_avatar.png';
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadUserProfile();
  } catch (err) {
    console.error(err);
    alert('Failed to load account');
  }

  document.getElementById('avatar_url').addEventListener('change', uploadAvatar);
  document.getElementById('profile_banner').addEventListener('change', () => {
    document.getElementById('banner-preview').src = document.getElementById('profile_banner').value;
  });

  document.getElementById('account-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await saveUserSettings();
    } catch (err) {
      alert(err.message);
    }
  });

  document.querySelector('#sessions-table').addEventListener('click', async (e) => {
    if (e.target.classList.contains('logout-session')) {
      const sid = e.target.dataset.id;
      await logoutSession(sid);
    }
  });
});

export { loadUserProfile, saveUserSettings, logoutSession, uploadAvatar };
