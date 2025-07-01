// Comment
// Project Name: Thronestead©
// File Name: notificationBell.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';

document.addEventListener('DOMContentLoaded', async () => {
  const bell = document.getElementById('nav-bell-icon');
  const list = document.getElementById('bell-dropdown');
  const badge = document.getElementById('nav-bell-count');

  if (!bell || !list || !badge) return;

  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;

  const headers = {
    'X-User-ID': session.user.id,
    Authorization: `Bearer ${session.access_token}`,
  };

  // Toggle dropdown and load latest
  bell.addEventListener('click', async () => {
    list.classList.toggle('show');
    if (list.classList.contains('show')) {
      await loadLatest();
    }
  });

  // Load top 5 recent notifications
  async function loadLatest() {
    try {
      const res = await fetch('/api/notifications/latest?limit=5', { headers });
      const data = await res.json();
      list.innerHTML = '';

      if (!data.notifications || data.notifications.length === 0) {
        list.innerHTML = '<div class="bell-item">No new notifications</div>';
        return;
      }

      data.notifications.forEach(n => {
        const item = document.createElement('div');
        item.className = 'bell-item';
        item.innerHTML = `
          <strong>${escapeHTML(n.title)}</strong><br/>
          <span class="bell-snippet">${escapeHTML(n.snippet || '')}</span>
        `;
        item.addEventListener('click', () => {
          if (n.url) window.location.href = n.url;
        });
        list.appendChild(item);
      });
    } catch (err) {
      console.error('❌ Failed to fetch latest notifications:', err);
      list.innerHTML = '<div class="bell-item">Failed to load</div>';
    }
  }

  // Fetch unread count
  async function fetchCount() {
    try {
      const res = await fetch('/api/navbar/counters', { headers });
      const data = await res.json();
      const count = (data.unread_notifications || 0);
      badge.textContent = count > 0 ? count : '';
    } catch (err) {
      console.error('❌ Failed to fetch notification count:', err);
    }
  }

  // Initial + scheduled poll
  await fetchCount();
  setInterval(fetchCount, 60000);

  // Optional: Real-time support
  supabase
    .channel('public:notifications')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'notifications', filter: `recipient_id=eq.${session.user.id}` },
      async () => {
        await fetchCount();
        if (list.classList.contains('show')) await loadLatest();
      }
    )
    .subscribe();
});

// Escape HTML utility
