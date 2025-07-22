// Project Name: Thronestead©
// File Name: communications_core.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';
import {
  showToast,
  authFetchJson,
  getValue,
  setText,
  escapeHTML,
  sanitizeHTML
} from './core_utils.js';

// Automatically initialize features based on available DOM elements
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('notification-feed')) initNotifications();
  if (document.getElementById('message-form') || document.getElementById('notice-form')) initCompose();
  if (document.getElementById('message-list') || document.getElementById('message-container')) initMessages();
});

// ---------------------- Notifications ----------------------
function initNotifications() {
  const feed = document.getElementById('notification-feed');
  const filterInput = document.getElementById('notification-filter');
  const categorySelect = document.getElementById('category-filter');
  const markAllBtn = document.getElementById('mark-all-btn');
  const clearAllBtn = document.getElementById('clear-all-btn');

  let currentNotifications = [];

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

  function updateTitle() {
    const count = currentNotifications.filter(n => !n.is_read).length;
    document.title = count ? `(${count}) Notifications | Thronestead` : 'Notifications | Thronestead';
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
      card.querySelector('.toggle-read-btn').addEventListener('click', e => {
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

  markAllBtn?.addEventListener('click', async () => {
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

  clearAllBtn?.addEventListener('click', async () => {
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

  filterInput?.addEventListener('input', applyFilters);
  categorySelect?.addEventListener('change', applyFilters);

  supabase
    .channel('notification-updates')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'notifications' }, fetchNotifications)
    .subscribe();

  fetchNotifications();
}

// ---------------------- Compose ----------------------
function initCompose() {
  let session;

  document.addEventListener('DOMContentLoaded', async () => {
    const { data: { session: s } } = await supabase.auth.getSession();
    if (!s) {
      window.location.href = 'login.html';
      return;
    }
    session = s;
    setupTabs();
    setupForms();
    prefillRecipient();
    loadRecipients();
  });

  function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');
    tabs.forEach(t => {
      t.addEventListener('click', () => {
        tabs.forEach(b => b.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));
        t.classList.add('active');
        document.getElementById(t.dataset.tab).classList.add('active');
      });
    });
  }

  function setupForms() {
    const msgForm = document.getElementById('message-form');
    const noticeForm = document.getElementById('notice-form');
    const treatyForm = document.getElementById('treaty-form');
    const warForm = document.getElementById('war-form');

    if (msgForm) {
      const preview = document.getElementById('msg-preview');
      msgForm.addEventListener('input', () => {
        setText('msg-preview', escapeHTML(getValue('msg-content')));
      });
      msgForm.addEventListener('submit', async e => {
        e.preventDefault();
        try {
          await authFetchJson('/api/compose/message', {
            method: 'POST',
            body: JSON.stringify({
              recipient_id: getValue('msg-recipient'),
              message: getValue('msg-content')
            })
          });
          showToast('Message sent');
          msgForm.reset();
          preview.textContent = '';
        } catch (err) {
          showToast(err.message);
        }
      });
    }

    if (noticeForm) {
      noticeForm.addEventListener('input', () => {
        setText('notice-preview', escapeHTML(getValue('notice-message')));
      });
      noticeForm.addEventListener('submit', async e => {
        e.preventDefault();
        try {
          await authFetchJson('/api/compose/notice', {
            method: 'POST',
            body: JSON.stringify({
              title: getValue('notice-title'),
              message: getValue('notice-message'),
              category: getValue('notice-category', true),
              link_action: getValue('notice-link', true),
              image_url: getValue('notice-image-url', true),
              expires_at: getValue('notice-expires', true)
            })
          });
          showToast('Notice created');
          noticeForm.reset();
          setText('notice-preview', '');
        } catch (err) {
          showToast(err.message);
        }
      });
    }

    if (treatyForm) {
      treatyForm.addEventListener('submit', async e => {
        e.preventDefault();
        try {
          await authFetchJson('/api/compose/treaty', {
            method: 'POST',
            body: JSON.stringify({
              partner_alliance_id: parseInt(getValue('treaty-partner')),
              treaty_type: getValue('treaty-type')
            })
          });
          showToast('Treaty proposed');
          treatyForm.reset();
        } catch (err) {
          showToast(err.message);
        }
      });
    }

    if (warForm) {
      warForm.addEventListener('input', () => {
        setText('war-preview', escapeHTML(getValue('war-reason')));
      });
      warForm.addEventListener('submit', async e => {
        e.preventDefault();
        try {
          await authFetchJson('/api/compose/war', {
            method: 'POST',
            body: JSON.stringify({
              defender_id: getValue('war-defender'),
              war_reason: getValue('war-reason')
            })
          });
          showToast('War declared');
          warForm.reset();
          setText('war-preview', '');
        } catch (err) {
          showToast(err.message);
        }
      });
    }
  }

  function prefillRecipient() {
    const params = new URLSearchParams(window.location.search);
    const val = params.get('recipient') || params.get('recipient_id');
    if (val) {
      const input = document.getElementById('msg-recipient');
      if (input) input.value = val;
    }
  }

  async function loadRecipients() {
    const list = document.getElementById('recipient-list');
    if (!list) return;
    try {
      const res = await authFetchJson('/api/players/lookup');
      res.players.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.user_id;
        opt.textContent = p.display_name;
        list.appendChild(opt);
      });
    } catch (err) {
      console.error('Failed to load recipients', err);
    }
  }
}

// ---------------------- Messages/Inbox ----------------------
function initMessages() {
  const list = document.getElementById('message-list');
  const countLabel = document.getElementById('message-count');
  const filterSelect = document.getElementById('category-filter');
  const markAllBtn = document.getElementById('mark-all-read');
  const prevBtns = document.querySelectorAll('.prev-page');
  const nextBtns = document.querySelectorAll('.next-page');
  const pageInfos = document.querySelectorAll('.page-info');
  const unreadToggle = document.getElementById('unread-only');

  let messages = [];
  let currentPage = 1;
  const pageSize = 10;
  let currentFilter = 'all';
  let showUnreadOnly = false;
  let session;

  const formatTime = iso => new Date(iso).toLocaleString();

  document.addEventListener('DOMContentLoaded', async () => {
    const { data: { session: s } } = await supabase.auth.getSession();
    if (!s) {
      if (list) list.innerHTML = '<p>❌ Login required to view messages.</p>';
      return;
    }
    session = s;
    if (list) {
      await loadInbox();
      subscribeToNewMessages(session.user.id);
      await applyKingdomLinks();
    }
    const container = document.getElementById('message-container');
    if (container) {
      const params = new URLSearchParams(window.location.search);
      const id = params.get('id') || params.get('message_id');
      if (id) {
        await loadMessageView(id);
        await applyKingdomLinks();
      } else {
        container.innerHTML = '<p>Invalid message.</p>';
      }
    }
    await applyKingdomLinks();
  });

  async function loadInbox() {
    let query = supabase
      .from('player_messages')
      .select('message_id, message, sent_at, is_read, category, users(username)')
      .eq('recipient_id', session.user.id)
      .order('sent_at', { ascending: false });
    if (currentFilter !== 'all') query = query.eq('category', currentFilter);
    if (showUnreadOnly) query = query.eq('is_read', false);
    const { data, error } = await query;
    if (error) {
      list.innerHTML = '<p>⚠️ Unable to load messages.</p>';
      return;
    }
    messages = (data || []).map(row => ({
      id: row.message_id,
      subject: row.message.slice(0, 50),
      sender_name: row.users?.username || 'Unknown',
      created_at: row.sent_at,
      is_read: row.is_read,
      message_type: row.category
    }));
    currentPage = 1;
    renderMessages();
  }

  function renderMessages() {
    list.innerHTML = '';
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const pageMessages = messages.slice(start, end);
    if (!pageMessages.length) {
      list.innerHTML = '<p>No messages found.</p>';
    } else {
      for (const msg of pageMessages) {
        const article = document.createElement('article');
        article.className = `message-item ${msg.is_read ? '' : 'unread'}`;
        article.innerHTML = `
          <a href="message.html?id=${msg.id}" class="message-link">
            <strong>${msg.subject}</strong>
            <span class="sender">From: ${msg.sender_name}</span>
            <span class="time">${formatTime(msg.created_at)}</span>
            <span class="type">${msg.message_type}</span>
          </a>
        `;
        list.appendChild(article);
      }
    }
    pageInfos.forEach(el => {
      el.textContent = `Page ${currentPage} of ${Math.ceil(messages.length / pageSize)}`;
    });
    if (countLabel) countLabel.textContent = `Total Messages: ${messages.length}`;
    prevBtns.forEach(btn => (btn.disabled = currentPage === 1));
    nextBtns.forEach(btn => (btn.disabled = end >= messages.length));
    applyKingdomLinks();
  }

  async function loadMessageView(id) {
    const container = document.getElementById('message-container');
    if (!container) return;
    container.innerHTML = '<p>Loading message...</p>';
    const { data, error } = await supabase
      .from('player_messages')
      .select('message, sent_at, is_read, category, users(username)')
      .eq('message_id', id)
      .single();
    if (error || !data) {
      container.innerHTML = '<p>Failed to load message.</p>';
      return;
    }
    await supabase.from('player_messages').update({ is_read: true }).eq('message_id', id);
    const replyLink = document.getElementById('reply-btn');
    if (replyLink) replyLink.href = `compose.html?recipient=${data.user_id}`;
    const bodyHtml = sanitizeHTML(marked.parse(data.message || ''));
    container.innerHTML = `
      <div class="message-meta">
        <strong>From:</strong> ${escapeHTML(data.users?.username || 'Unknown')}<br>
        <strong>Date:</strong> ${formatTime(data.sent_at)}
      </div>
      <h3 class="message-subject">${escapeHTML(data.subject || '')}</h3>
      <div class="message-body">${bodyHtml}</div>
    `;
    applyKingdomLinks();
  }

  async function markAllAsRead() {
    const ids = messages.filter(m => !m.is_read).map(m => m.id);
    if (!ids.length) return;
    const { error } = await supabase
      .from('player_messages')
      .update({ is_read: true })
      .in('message_id', ids);
    if (!error) {
      messages.forEach(m => (m.is_read = true));
      renderMessages();
    }
  }

  function subscribeToNewMessages(uid) {
    supabase
      .channel(`inbox-${uid}`)
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'player_messages', filter: `recipient_id=eq.${uid}` }, loadInbox)
      .subscribe();
  }

  filterSelect?.addEventListener('change', () => {
    currentFilter = filterSelect.value;
    loadInbox();
  });
  markAllBtn?.addEventListener('click', markAllAsRead);
  unreadToggle?.addEventListener('change', () => {
    showUnreadOnly = unreadToggle.checked;
    loadInbox();
  });
  prevBtns.forEach(btn => btn.addEventListener('click', () => {
    currentPage--;
    renderMessages();
  }));
  nextBtns.forEach(btn => btn.addEventListener('click', () => {
    currentPage++;
    renderMessages();
  }));
}

export { initCompose, initMessages, initNotifications };

