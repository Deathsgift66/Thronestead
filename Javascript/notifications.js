// Project Name: Thronestead©
// File Name: notifications.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { showToast } from './utils.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';

const feed = document.getElementById('notification-feed');
const filterInput = document.getElementById('notification-filter');
const categorySelect = document.getElementById('category-filter');
const markAllBtn = document.getElementById('mark-all-btn');
const clearAllBtn = document.getElementById('clear-all-btn');

let currentNotifications = [];

document.addEventListener('DOMContentLoaded', () => {
  applyKingdomLinks();
});

function updateTitle() {
  const count = currentNotifications.filter(n => !n.is_read).length;
  document.title = count ? `(${count}) Notifications | Thronestead` : 'Notifications | Thronestead';
}

async function fetchNotifications() {
  const user = await supabase.auth.getUser();
  const userId = user.data?.user?.id;

  const { data, error } = await supabase
    .from('notifications')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Fetch error:', error);
    showToast('Failed to load notifications');
    return;
  }

  currentNotifications = data;
  renderNotifications(currentNotifications);
  applyKingdomLinks();
  updateTitle();
}

function renderNotifications(data) {
  feed.innerHTML = '';

  if (!data.length) {
    feed.innerHTML = '<p class="no-notifications">No notifications available.</p>';
    return;
  }

  for (const n of data) {
    const card = document.createElement('div');
    card.classList.add('notification-card');
    card.setAttribute('aria-label', 'notification card');
    if (!n.is_read) card.classList.add('unread');

    const toggleText = n.is_read ? 'Mark Unread' : 'Mark Read';

    card.innerHTML = `
      <div class="notification-header">
        <strong>${n.title}</strong>
        <span class="priority-tag ${n.priority}">${n.priority}</span>
      </div>
      <p class="notification-body">${n.message}</p>
      <div class="notification-footer">
        <small>${new Date(n.created_at).toLocaleString()}</small>
        ${n.link_action ? `<a href="${n.link_action}" class="notification-link">View</a>` : ''}
        <button class="toggle-read-btn" data-id="${n.notification_id}" data-read="${n.is_read}">${toggleText}</button>
      </div>
    `;

    card.querySelector('.toggle-read-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      toggleRead(n.notification_id, !n.is_read);
    });

    feed.appendChild(card);
  }
  applyKingdomLinks();
}

async function toggleRead(notificationId, readState) {
  const { error } = await supabase
    .from('notifications')
    .update({ is_read: readState })
    .eq('notification_id', notificationId);

  if (error) {
    console.error('Mark read failed:', error);
    showToast('Could not update notification');
  }
  fetchNotifications();
}

markAllBtn.addEventListener('click', async () => {
  const user = await supabase.auth.getUser();
  const { error } = await supabase
    .from('notifications')
    .update({ is_read: true })
    .eq('user_id', user.data.user.id);

  if (error) {
    console.error('Mark all failed:', error);
    showToast('Failed to mark all read');
  }
  fetchNotifications();
});

clearAllBtn.addEventListener('click', async () => {
  const user = await supabase.auth.getUser();
  const { error } = await supabase
    .from('notifications')
    .delete()
    .eq('user_id', user.data.user.id);

  if (error) {
    console.error('Clear failed:', error);
    showToast('Failed to clear notifications');
  }
  fetchNotifications();
});

function applyFilters() {
  const keyword = filterInput.value.toLowerCase();
  const cat = categorySelect.value;
  const filtered = currentNotifications.filter(n => {
    const matchesText = n.title.toLowerCase().includes(keyword) || n.message.toLowerCase().includes(keyword);
    const matchesCat = !cat || n.category === cat;
    return matchesText && matchesCat;
  });
  renderNotifications(filtered);
}

filterInput.addEventListener('input', applyFilters);
categorySelect.addEventListener('change', applyFilters);

supabase
  .channel('notification-updates')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'notifications' }, () => {
    fetchNotifications();
  })
  .subscribe();

fetchNotifications();
