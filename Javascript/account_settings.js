// Project Name: Kingmakers Rise©
// File Name: account_settings.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import {
  showToast,
  validateEmail,
  escapeHTML,
  setValue,
  setSrc,
  setText,
  fragmentFrom,
  isValidURL
} from './utils.js';

/**
 * Retrieve headers for authenticated Supabase API calls.
 * Ensures user and session are valid and returns headers with auth tokens.
 */
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

/**
 * Loads user profile data and updates the UI with user settings and session history.
 */
async function loadUserProfile() {
  const headers = await authHeaders();
  const res = await fetch('/api/account/profile', { headers });
  if (!res.ok) throw new Error('Failed to load profile');
  const info = await res.json();

  // Profile fields from users table
  setSrc('avatar-preview', info.profile_picture_url || 'Assets/avatars/default_avatar_emperor.png');
  setValue('avatar_url', info.profile_picture_url || '');
  setValue('display_name', info.display_name || '');
  setValue('motto', info.motto || '');
  setValue('profile_bio', info.bio || '');
  setValue('email', info.email);
  setValue('profile_banner', info.profile_banner || '');
  setSrc('banner-preview', info.profile_banner || 'Assets/profile_background.png');
  setValue('theme_preference', info.theme_preference || 'parchment');

  const theme = document.getElementById('theme_preference')?.value;
  if (theme) document.body.dataset.theme = theme;

  setText('last_login', `Last Login: ${info.last_login_at || 'Unknown'}`);

  const ipEl = document.getElementById('ip_alerts');
  if (ipEl) ipEl.checked = !!info.ip_login_alerts;
  const emailEl = document.getElementById('email_confirmations');
  if (emailEl) emailEl.checked = !!info.email_login_confirmations;

  // VIP / Founder Status
  const vipElement = document.getElementById('vip-status');
  if (vipElement) {
    vipElement.innerText = info.vip_level ? `VIP ${info.vip_level}` : 'Not a VIP';
    if (info.founder) vipElement.innerText += ' (Founder)';
  }

  // Session list
  const tbody = document.querySelector('#sessions-table tbody');
  if (!tbody || !info.sessions) return;
  tbody.innerHTML = '';
  const rows = fragmentFrom(info.sessions, (s) => {
    const row = document.createElement('tr');
    row.id = `session-${s.session_id}`;
    row.innerHTML = `
      <td>${escapeHTML(s.device)}</td>
      <td>${escapeHTML(s.last_seen)}</td>
      <td><button class="logout-session" data-id="${s.session_id}">Logout</button></td>`;
    return row;
  });
  tbody.appendChild(rows);
}

/**
 * Loads kingdom details for the authenticated user and updates the form fields.
 */
async function loadKingdomDetails() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user?.id) return;

  const { data, error } = await supabase
    .from('kingdoms')
    .select('ruler_title,banner_url,emblem_url')
    .eq('user_id', session.user.id)
    .single();

  if (error || !data) return;

  setValue('ruler_title', data.ruler_title || '');
  setValue('kingdom_banner_url', data.banner_url || '');
  setValue('kingdom_emblem_url', data.emblem_url || '');
}

/**
 * Saves changes to the user's profile and kingdom fields.
 */
async function saveUserSettings() {
  const headers = await authHeaders();
  const displayName = document.getElementById('display_name')?.value.trim() || '';
  const email = document.getElementById('email')?.value.trim() || '';

  if (displayName.length < 3) {
    showToast('Display Name must be at least 3 characters.');
    return;
  }
  if (!validateEmail(email)) {
    showToast('Please enter a valid email.');
    return;
  }

  const payload = {
    display_name: displayName,
    motto: document.getElementById('motto')?.value || '',
    bio: document.getElementById('profile_bio')?.value || '',
    profile_picture_url: document.getElementById('avatar_url')?.value || '',
    theme_preference: document.getElementById('theme_preference')?.value || '',
    profile_banner: document.getElementById('profile_banner')?.value || '',
    ip_login_alerts: !!document.getElementById('ip_alerts')?.checked,
    email_login_confirmations: !!document.getElementById('email_confirmations')?.checked,
    email: email
  };

  const res = await fetch('/api/account/update', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to save');

  // Update kingdom-specific data
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
        ruler_title: document.getElementById('ruler_title')?.value.trim() || '',
        banner_url: document.getElementById('kingdom_banner_url')?.value.trim() || null,
        emblem_url: document.getElementById('kingdom_emblem_url')?.value.trim() || null
      })
    });
  }

  showToast('Settings saved');
}

/**
 * Sends a request to log out a specific session.
 */
async function logoutSession(sessionId) {
  const headers = await authHeaders();
  await fetch('/api/account/logout-session', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  document.getElementById(`session-${sessionId}`)?.remove();
}

/**
 * Updates avatar preview image.
 */
function uploadAvatar() {
  const url = document.getElementById('avatar_url')?.value;
  const preview = document.getElementById('avatar-preview');
  if (!preview) return;
  if (url && !isValidURL(url)) {
    showToast('Invalid avatar URL');
    preview.src = 'Assets/avatars/default_avatar_emperor.png';
  } else {
    preview.src = url || 'Assets/avatars/default_avatar_emperor.png';
  }
}

/**
 * Subscribes to Supabase realtime changes on the user's session table.
 */
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

/**
 * Main page load handler.
 */
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

  document.getElementById('avatar_url')?.addEventListener('change', uploadAvatar);

  document.getElementById('profile_banner')?.addEventListener('change', () => {
    const bannerEl = document.getElementById('profile_banner');
    const previewEl = document.getElementById('banner-preview');
    if (bannerEl && previewEl) previewEl.src = bannerEl.value;
  });

  document.getElementById('theme_preference')?.addEventListener('change', (e) => {
    document.body.dataset.theme = e.target.value;
  });

  document.getElementById('account-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await saveUserSettings();
    } catch (err) {
      showToast(err.message);
    }
  });

  document.querySelector('#sessions-table')?.addEventListener('click', async (e) => {
    if (e.target.classList.contains('logout-session')) {
      const sid = e.target.dataset.id;
      await logoutSession(sid);
    }
  });
});


export { loadUserProfile, loadKingdomDetails, saveUserSettings, logoutSession, uploadAvatar, subscribeSessions };
