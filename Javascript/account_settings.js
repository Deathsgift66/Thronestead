import { supabase } from './supabaseClient.js';

async function authHeaders() {
  const [{ data: { user } }, { data: { session } }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession()
  ]);
  if (!user || !session) throw new Error('Unauthorized');
  return {
    'X-User-ID': user.id,
    Authorization: `Bearer ${session.access_token}`
  };
}

async function loadUserProfile() {
  const headers = await authHeaders();
  const res = await fetch('/api/account/profile', { headers });
  if (!res.ok) throw new Error('Failed to load profile');
  const info = await res.json();

  document.getElementById('avatar-preview').src = info.profile_picture_url || 'Assets/avatars/default_avatar_emperor.png';
  document.getElementById('avatar_url').value = info.profile_picture_url || '';
  document.getElementById('display_name').value = info.display_name || '';
  document.getElementById('motto').value = info.motto || '';
  document.getElementById('profile_bio').value = info.bio || '';
  document.getElementById('email').value = info.email;
  document.getElementById('profile_banner').value = info.profile_banner || '';
  document.getElementById('banner-preview').src = info.profile_banner || 'Assets/profile_background.png';
  document.getElementById('theme_preference').value = info.theme_preference || 'parchment';
  document.body.dataset.theme = document.getElementById('theme_preference').value;
  document.getElementById('last_login').textContent = `Last Login: ${info.last_login_at || 'Unknown'}`;
  document.getElementById('ip_alerts').checked = !!info.ip_login_alerts;
  document.getElementById('email_confirmations').checked = !!info.email_login_confirmations;
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

async function loadKingdomDetails() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  const { data, error } = await supabase
    .from('kingdoms')
    .select('ruler_title,banner_url,emblem_url')
    .eq('owner_id', session.user.id)
    .single();
  if (error || !data) return;
  document.getElementById('ruler_title').value = data.ruler_title || '';
  document.getElementById('kingdom_banner_url').value = data.banner_url || '';
  document.getElementById('kingdom_emblem_url').value = data.emblem_url || '';
}

async function saveUserSettings() {
  const headers = await authHeaders();
  const displayName = document.getElementById('display_name').value.trim();
  const email = document.getElementById('email').value.trim();
  const payload = {
    display_name: displayName,
    motto: document.getElementById('motto').value,
    bio: document.getElementById('profile_bio').value,
    profile_picture_url: document.getElementById('avatar_url').value,
    theme_preference: document.getElementById('theme_preference').value,
    profile_banner: document.getElementById('profile_banner').value,
    ip_login_alerts: document.getElementById('ip_alerts').checked,
    email_login_confirmations: document.getElementById('email_confirmations').checked,
  };

  if (displayName.length < 3) {
    showToast('Display Name must be at least 3 characters.');
    return;
  }
  if (!validateEmail(email)) {
    showToast('Please enter a valid email.');
    return;
  }
  payload.email = email;
  const res = await fetch('/api/account/update', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to save');

  const [{ data: { user } }, { data: { session } }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession()
  ]);
  if (user && session) {
    await fetch('/api/kingdom/update', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': user.id,
        Authorization: `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        ruler_title: document.getElementById('ruler_title').value.trim(),
        banner_url:
          document.getElementById('kingdom_banner_url').value.trim() || null,
        emblem_url:
          document.getElementById('kingdom_emblem_url').value.trim() || null
      })
    });
  }
  showToast('Settings saved');
}

async function logoutSession(sessionId) {
  const headers = await authHeaders();
  await fetch('/api/account/logout-session', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  document.getElementById(`session-${sessionId}`).remove();
}

function uploadAvatar() {
  const url = document.getElementById('avatar_url').value;
  document.getElementById('avatar-preview').src = url || 'Assets/avatars/default_avatar_emperor.png';
}

function subscribeSessions(userId) {
  supabase
    .channel('user_sessions')
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'user_active_sessions', filter: `user_id=eq.${userId}` },
      loadUserProfile
    )
    .subscribe();
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadUserProfile();
    await loadKingdomDetails();
    const { data: { user } } = await supabase.auth.getUser();
    if (user) subscribeSessions(user.id);
  } catch (err) {
    console.error(err);
    showToast('Failed to load account');
  }

  document.getElementById('avatar_url').addEventListener('change', uploadAvatar);
  document.getElementById('profile_banner').addEventListener('change', () => {
    document.getElementById('banner-preview').src = document.getElementById('profile_banner').value;
  });
  document.getElementById('theme_preference').addEventListener('change', (e) => {
    document.body.dataset.theme = e.target.value;
  });

  document.getElementById('account-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await saveUserSettings();
    } catch (err) {
      showToast(err.message);
    }
  });

  document.querySelector('#sessions-table').addEventListener('click', async (e) => {
    if (e.target.classList.contains('logout-session')) {
      const sid = e.target.dataset.id;
      await logoutSession(sid);
    }
  });
});

export { loadUserProfile, loadKingdomDetails, saveUserSettings, logoutSession, uploadAvatar, subscribeSessions };

function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

function showToast(msg) {
  const toastEl = document.getElementById('toast');
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  setTimeout(() => {
    toastEl.classList.remove('show');
  }, 3000);
}
