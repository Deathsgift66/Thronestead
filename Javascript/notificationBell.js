/*
Project Name: Kingmakers Rise Frontend
File Name: notificationBell.js
Date: June 2, 2025
Author: ChatGPT
*/
import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  const bell = document.getElementById('nav-bell-icon');
  const list = document.getElementById('bell-dropdown');
  const badge = document.getElementById('nav-bell-count');
  if (!bell || !list) return;

  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  const headers = {
    'X-User-ID': session.user.id,
    Authorization: `Bearer ${session.access_token}`,
  };

  bell.addEventListener('click', async () => {
    list.classList.toggle('show');
    if (list.classList.contains('show')) {
      await loadLatest();
    }
  });

  async function loadLatest() {
    try {
      const res = await fetch('/api/notifications/latest?limit=5', { headers });
      const data = await res.json();
      list.innerHTML = '';
      data.notifications.forEach(n => {
        const item = document.createElement('div');
        item.className = 'bell-item';
        item.textContent = n.title;
        list.appendChild(item);
      });
    } catch (err) {
      console.error('Failed to fetch latest notifications', err);
    }
  }

  async function fetchCount() {
    try {
      const res = await fetch('/api/navbar/counters', { headers });
      const data = await res.json();
      badge.textContent = data.unread_notifications > 0 ? data.unread_notifications : '';
    } catch (err) {
      console.error('Failed to fetch counts', err);
    }
  }

  await fetchCount();
  setInterval(fetchCount, 60000);
});
