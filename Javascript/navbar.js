// Project Name: Thronestead©
// File Name: navbar.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  const picEl = document.getElementById('nav-profile-pic');
  const nameEl = document.getElementById('nav-username');
  const badgeEl = document.getElementById('nav-unread');

  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      console.warn("⚠️ No active session. Navbar profile not loaded.");
      return;
    }

    const headers = {
      'X-User-ID': session.user.id,
      Authorization: `Bearer ${session.access_token}`
    };

    // Fetch basic profile info
    const res = await fetch('/api/navbar/profile', { headers });
    if (!res.ok) throw new Error(`Profile fetch failed: ${res.status}`);
    const data = await res.json();

    if (nameEl) nameEl.textContent = data.username || 'Unknown';
    if (picEl && data.profile_picture_url) picEl.src = data.profile_picture_url;

    // Initialize badge count
    if (badgeEl) badgeEl.textContent = (data.unread_messages > 0) ? data.unread_messages : '';

    // Begin polling for dynamic updates
    pollCounters(headers, badgeEl);

  } catch (err) {
    console.error('❌ Failed to load navbar profile:', err);
    if (nameEl) nameEl.textContent = 'Guest';
    if (badgeEl) badgeEl.textContent = '';
  }
});

/**
 * Poll unread counters and update badge display every 60 seconds.
 * @param {Object} headers - Auth headers.
 * @param {HTMLElement} badgeEl - Badge DOM element.
 */
async function pollCounters(headers, badgeEl) {
  const fetchCounters = async () => {
    try {
      const res = await fetch('/api/navbar/counters', { headers });
      if (!res.ok) throw new Error(`Counters fetch failed: ${res.status}`);
      const data = await res.json();

      const total = (data.unread_messages || 0) + (data.unread_notifications || 0);
      if (badgeEl) badgeEl.textContent = total > 0 ? total : '';
    } catch (err) {
      console.warn('⚠️ Failed to fetch navbar counters:', err);
    }
  };

  await fetchCounters();
  setInterval(fetchCounters, 60000); // Refresh every 60s
}
