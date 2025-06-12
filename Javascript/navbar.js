import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  const picEl = document.getElementById('nav-profile-pic');
  const nameEl = document.getElementById('nav-username');
  const badgeEl = document.getElementById('nav-unread');

  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;

  const headers = {
    'X-User-ID': session.user.id,
    Authorization: `Bearer ${session.access_token}`
  };

  try {
    const res = await fetch('/api/navbar/profile', { headers });
    const data = await res.json();
    if (nameEl) nameEl.textContent = data.username || 'Unknown';
    if (picEl && data.profile_picture_url) picEl.src = data.profile_picture_url;
    if (badgeEl) badgeEl.textContent = data.unread_messages > 0 ? data.unread_messages : '';
    pollCounters(headers, badgeEl);
  } catch (err) {
    console.error('Failed to load navbar profile', err);
  }
});

async function pollCounters(headers, badgeEl) {
  async function fetchCounters() {
    try {
      const res = await fetch('/api/navbar/counters', { headers });
      const data = await res.json();
      if (badgeEl) {
        const total = (data.unread_messages || 0) + (data.unread_notifications || 0);
        badgeEl.textContent = total > 0 ? total : '';
      }
    } catch (err) {
      console.error('Failed to fetch counters', err);
    }
  }
  await fetchCounters();
  setInterval(fetchCounters, 60000);
}
