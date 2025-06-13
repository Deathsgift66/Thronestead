/*
Project Name: Kingmakers Rise Frontend
File Name: messages.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Unified Messaging System — Inbox + View + Compose

import { supabase } from './supabaseClient.js';

let currentSession;
let allMessages = [];

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  currentSession = session;

  if (document.getElementById("message-list")) {
    await loadInbox(session);
    subscribeToNewMessages(session.user.id);
    const filter = document.getElementById('category-filter');
    if (filter) filter.addEventListener('change', () => filterMessages(filter.value));
    const markBtn = document.getElementById('mark-all-read');
    if (markBtn) markBtn.addEventListener('click', async () => {
      if (!confirm('Mark all messages read?')) return;
      await markAllRead();
      await loadInbox(session);
    });
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

// ✅ Load Inbox
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
    if (!res.ok) throw new Error('Failed');
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
  if (!list || list.length === 0) {
    container.innerHTML = '<p>No messages found.</p>';
    return;
  }
  list.forEach(msg => {
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

function subscribeToNewMessages(uid) {
  const channel = supabase.channel(`inbox-${uid}`);
  channel
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'player_messages', filter: `recipient_id=eq.${uid}` },
      async () => {
        // Simple refresh on new message
        if (currentSession) {
          await loadInbox(currentSession);
        }
      }
    )
    .subscribe();
}

// ✅ Load Message View
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
        <strong>From:</strong> ${escapeHTML(data.username || "Unknown")}
        <br>
        <strong>Date:</strong> ${formatDate(data.sent_at)}
      </div>
      <h3>${escapeHTML(data.subject || '')}</h3>
      <div class="message-body">
        ${formatIcons(marked.parse(data.message || ''))}
      </div>
      <div class="message-actions">
        <a href="compose.html?reply_to=${data.user_id}" class="action-btn">Reply</a>
        <button class="action-btn" id="delete-message">Delete</button>
        <button class="action-btn" id="report-message">Report</button>
      </div>
    `;

    // ✅ Bind Delete button
    document.getElementById("delete-message").addEventListener("click", async () => {
      if (!confirm("Are you sure you want to delete this message?")) return;

      try {
        const resp = await fetch('/api/messages/delete', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
            'X-User-ID': session.user.id
          },
          body: JSON.stringify({ message_id: messageId })
        });
        if (!resp.ok) throw new Error();

        alert("Message deleted.");
        window.location.href = "messages.html";
      } catch (err) {
        console.error("❌ Error deleting message:", err);
        alert("Failed to delete message.");
      }
    });

    // ✅ Bind Report button (optional API call)
    document.getElementById("report-message").addEventListener("click", async () => {
      alert("Report submitted! (stub — implement backend API for moderation)");
    });

  } catch (err) {
    console.error("❌ Error loading message:", err);
    container.innerHTML = "<p>Failed to load message.</p>";
  }
}

// ✅ Setup Compose
function setupCompose(session) {
  const composeForm = document.getElementById("compose-form");

  // ✅ If replying to someone
  const urlParams = new URLSearchParams(window.location.search);
  const replyTo = urlParams.get("reply_to");

  if (replyTo) {
    document.getElementById("recipient").value = replyTo;
    document.getElementById("recipient").disabled = true;
  }

  composeForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const recipient = document.getElementById("recipient").value.trim();
    const subject = document.getElementById("subject").value.trim();
    const messageContent = document.getElementById("message-content").value.trim();
    const category = document.getElementById("category")?.value || "player";

    if (!recipient || !messageContent) {
      alert("Please enter both recipient and message.");
      return;
    }

    try {
      const res = await fetch('/api/messages/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
          'X-User-ID': session.user.id
        },
        body: JSON.stringify({
          recipient: recipient,
          subject: subject || null,
          content: messageContent,
          sender_id: session.user.id,
          category: category
        })
      });

      if (!res.ok) throw new Error('send failed');

      alert("Message sent!");
      window.location.href = "messages.html";

    } catch (err) {
      console.error("❌ Error sending message:", err);
      alert("Failed to send message.");
    }
  });
}

// ✅ Date formatting
function formatDate(ts) {
  if (!ts) return "Unknown";
  const date = new Date(ts);
  return date.toLocaleString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });
}

// ✅ Basic HTML escape
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatIcons(html) {
  return html
    .replace(/:sword:/g, '<img src="Assets/icon-sword.svg" class="icon" alt="sword">')
    .replace(/:gold:/g, '<img src="Assets/icon-bell.svg" class="icon" alt="gold">');
}

// ✅ Real-time subscription
function subscribeToMessages(userId, callback) {
  supabase
    .channel('messages:' + userId)
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'player_messages', filter: `recipient_id=eq.${userId}` },
      async payload => {
        await callback(payload);
      }
    )
    .subscribe();
}

function filterMessages(category) {
  if (category === 'all') {
    renderMessages(allMessages);
  } else {
    renderMessages(allMessages.filter(m => m.category === category));
  }
}

async function markAllRead() {
  try {
    const res = await fetch('/api/messages/mark_all_read', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${currentSession.access_token}`,
        'X-User-ID': currentSession.user.id
      }
    });
    if (!res.ok) throw new Error('Failed');
    alert('All messages marked read');
  } catch (err) {
    console.error('❌ Error marking all read:', err);
    alert('Failed to mark all read');
  }
}

function bindSwipe(card, messageId) {
  let startX;
  card.addEventListener('touchstart', e => { startX = e.touches[0].clientX; });
  card.addEventListener('touchmove', e => {
    if (!startX) return;
    const diff = e.touches[0].clientX - startX;
    if (diff < -60) {
      card.classList.add('swipe-delete');
    }
  });
  card.addEventListener('touchend', async () => {
    if (card.classList.contains('swipe-delete')) {
      if (confirm('Delete this message?')) {
        await fetch('/api/messages/delete', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${currentSession.access_token}`,
            'X-User-ID': currentSession.user.id
          },
          body: JSON.stringify({ message_id: messageId })
        });
        await loadInbox(currentSession);
      }
    }
    card.classList.remove('swipe-delete');
    startX = null;
  });
}
