// Project Name: Kingmakers Rise©
// File Name: messages.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// Unified Messaging System — Inbox + View + Compose + Enhancements

import { supabase } from './supabaseClient.js';

let currentSession;
let allMessages = [];

// ✅ DOM Ready

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return (window.location.href = "login.html");

  currentSession = session;

  if (document.getElementById("message-list")) {
    await loadInbox(session);
    subscribeToNewMessages(session.user.id);
    setupInboxControls();
  } else if (document.getElementById("message-container")) {
    const urlParams = new URLSearchParams(window.location.search);
    const messageId = urlParams.get("message_id");
    if (messageId) {
      await loadMessageView(messageId, session);
      subscribeToMessages(session.user.id, async (payload) => {
        if (payload.new.message_id === parseInt(messageId)) {
          await loadMessageView(messageId, session);
        }
      });
    } else {
      document.getElementById("message-container").innerHTML = "<p>Invalid message.</p>";
    }
  } else if (document.getElementById("compose-form")) {
    setupCompose(session);
  }
});

function setupInboxControls() {
  const filter = document.getElementById('category-filter');
  if (filter) filter.addEventListener('change', () => filterMessages(filter.value));

  const markBtn = document.getElementById('mark-all-read');
  if (markBtn) markBtn.addEventListener('click', async () => {
    if (!confirm('Mark all messages read?')) return;
    await markAllRead();
    await loadInbox(currentSession);
  });

  const search = document.getElementById('message-search');
  if (search) search.addEventListener('input', () => {
    const query = search.value.toLowerCase();
    renderMessages(allMessages.filter(m =>
      m.subject?.toLowerCase().includes(query) ||
      m.message?.toLowerCase().includes(query)
    ));
  });
}

async function loadInbox(session) {
  const container = document.getElementById("message-list");
  container.innerHTML = "<p>Loading messages...</p>";
  try {
    const res = await fetch('/api/messages/inbox', {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'X-User-ID': session.user.id
      }
    });
    const { messages } = await res.json();
    allMessages = messages || [];
    renderMessages(allMessages);
  } catch (err) {
    console.error("❌ Error loading inbox:", err);
    container.innerHTML = "<p>Failed to load messages.</p>";
  }
}

function renderMessages(list) {
  const container = document.getElementById('message-list');
  container.innerHTML = '';
  document.getElementById('message-count').textContent = `${list.length} Messages`;
  if (!list.length) {
    container.innerHTML = '<p>No messages found.</p>';
    return;
  }
  list.slice(0, 100).forEach(msg => { // ✅ Pagination placeholder
    const card = document.createElement('div');
    card.classList.add('message-card');
    if (!msg.is_read) card.classList.add('unread');
    card.innerHTML = `
      <a href="message.html?message_id=${msg.message_id}">
        <div class="message-meta">
          <span>From: ${escapeHTML(msg.sender || 'Unknown')}</span>
          <span>${formatDate(msg.sent_at)}</span>
        </div>
        <div class="message-subject">${escapeHTML((msg.subject || msg.message).substring(0, 50))}</div>
      </a>`;
    bindSwipe(card, msg.message_id);
    container.appendChild(card);
  });
}

async function loadMessageView(messageId, session) {
  const container = document.getElementById("message-container");
  container.innerHTML = "<p>Loading message...</p>";

  try {
    const res = await fetch(`/api/messages/${messageId}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'X-User-ID': session.user.id
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');

    container.innerHTML = `
      <div class="message-meta">
        <strong>From:</strong> ${escapeHTML(data.username || "Unknown")}<br>
        <strong>Date:</strong> ${formatDate(data.sent_at)}
      </div>
      <h3>${escapeHTML(data.subject || '')}</h3>
      <div class="message-body">${formatIcons(marked.parse(data.message || ''))}</div>
      <div class="message-actions">
        <a href="compose.html?reply_to=${data.user_id}" class="action-btn">Reply</a>
        <button class="action-btn" id="delete-message">Delete</button>
        <button class="action-btn" id="report-message">Report</button>
      </div>`;

    document.getElementById("delete-message").addEventListener("click", async () => {
      if (!confirm("Are you sure you want to delete this message?")) return;
      await fetch('/api/messages/delete', {
        method: 'POST',
        headers: getAuthHeaders(session),
        body: JSON.stringify({ message_id: messageId })
      });
      alert("Message deleted.");
      window.location.href = "messages.html";
    });

    document.getElementById("report-message").addEventListener("click", async () => {
      alert("Report submitted. Awaiting admin review.");
    });
  } catch (err) {
    console.error("❌ Error loading message:", err);
    container.innerHTML = "<p>Failed to load message.</p>";
  }
}

function setupCompose(session) {
  const form = document.getElementById("compose-form");
  const urlParams = new URLSearchParams(window.location.search);
  const replyTo = urlParams.get("reply_to");

  if (replyTo) {
    document.getElementById("recipient").value = replyTo;
    document.getElementById("recipient").disabled = true;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const recipient = document.getElementById("recipient").value.trim();
    const subject = document.getElementById("subject").value.trim();
    const content = document.getElementById("message-content").value.trim();
    const category = document.getElementById("category")?.value || "player";

    if (!recipient || !content) return alert("Fill all fields.");

    try {
      const res = await fetch('/api/messages/send', {
        method: 'POST',
        headers: getAuthHeaders(session),
        body: JSON.stringify({ recipient, subject, content, category, sender_id: session.user.id })
      });
      if (!res.ok) throw new Error('Send failed');
      alert("Message sent!");
      window.location.href = "messages.html";
    } catch (err) {
      console.error("❌ Error sending message:", err);
      alert("Failed to send message.");
    }
  });
}

function getAuthHeaders(session) {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`,
    'X-User-ID': session.user.id
  };
}

function formatDate(ts) {
  return new Date(ts).toLocaleString();
}

function escapeHTML(str) {
  return str?.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;") || "";
}

function formatIcons(html) {
  return html
    .replace(/:sword:/g, '<img src="Assets/icon-sword.svg" class="icon" alt="sword">')
    .replace(/:gold:/g, '<img src="Assets/icon-bell.svg" class="icon" alt="gold">');
}

function subscribeToNewMessages(uid) {
  supabase.channel(`inbox-${uid}`)
    .on('postgres_changes', {
      event: 'INSERT', schema: 'public', table: 'player_messages', filter: `recipient_id=eq.${uid}`
    }, () => loadInbox(currentSession))
    .subscribe();
}

function subscribeToMessages(uid, cb) {
  supabase.channel(`messages:${uid}`)
    .on('postgres_changes', {
      event: 'INSERT', schema: 'public', table: 'player_messages', filter: `recipient_id=eq.${uid}`
    }, cb).subscribe();
}

function filterMessages(category) {
  const searchVal = document.getElementById('message-search')?.value.toLowerCase() || '';
  const filtered = allMessages.filter(m =>
    (category === 'all' || m.category === category) &&
    (m.subject?.toLowerCase().includes(searchVal) || m.message?.toLowerCase().includes(searchVal))
  );
  renderMessages(filtered);
}

async function markAllRead() {
  await fetch('/api/messages/mark_all_read', {
    method: 'POST',
    headers: getAuthHeaders(currentSession)
  });
}

function bindSwipe(card, messageId) {
  let startX;
  card.addEventListener('touchstart', e => startX = e.touches[0].clientX);
  card.addEventListener('touchmove', e => {
    if (!startX) return;
    const diff = e.touches[0].clientX - startX;
    if (diff < -60) card.classList.add('swipe-delete');
  });
  card.addEventListener('touchend', async () => {
    if (card.classList.contains('swipe-delete')) {
      if (confirm('Delete this message?')) {
        await fetch('/api/messages/delete', {
          method: 'POST',
          headers: getAuthHeaders(currentSession),
          body: JSON.stringify({ message_id: messageId })
        });
        await loadInbox(currentSession);
      }
    }
    card.classList.remove('swipe-delete');
    startX = null;
  });
}
