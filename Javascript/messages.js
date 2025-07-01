// Project Name: Thronestead©
// File Name: messages.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Inbox Viewer + Controls

import { supabase } from '../supabaseClient.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';

const list = document.getElementById('message-list');
const countLabel = document.getElementById('message-count');
const filterSelect = document.getElementById('category-filter');
const markAllBtn = document.getElementById('mark-all-read');
const prevBtn = document.getElementById('prev-page');
const nextBtn = document.getElementById('next-page');
const pageInfo = document.getElementById('page-info');

let messages = [];
let currentPage = 1;
const pageSize = 10;
let currentFilter = 'all';
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

  pageInfo.textContent = `Page ${currentPage} of ${Math.ceil(messages.length / pageSize)}`;
  countLabel.textContent = `Total Messages: ${messages.length}`;
  prevBtn.disabled = currentPage === 1;
  nextBtn.disabled = end >= messages.length;
  applyKingdomLinks();
}

async function loadMessageView(id) {
  const container = document.getElementById('message-container');
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

  container.innerHTML = `
    <div class="message-meta">
      <strong>From:</strong> ${data.users?.username || 'Unknown'}<br>
      <strong>Date:</strong> ${formatTime(data.sent_at)}
    </div>
    <div class="message-body">${data.message}</div>
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
  supabase.channel(`inbox-${uid}`)
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'player_messages', filter: `recipient_id=eq.${uid}` }, loadInbox)
    .subscribe();
}

filterSelect?.addEventListener('change', () => {
  currentFilter = filterSelect.value;
  loadInbox();
});

markAllBtn?.addEventListener('click', markAllAsRead);
prevBtn?.addEventListener('click', () => {
  currentPage--;
  renderMessages();
});
nextBtn?.addEventListener('click', () => {
  currentPage++;
  renderMessages();
});
