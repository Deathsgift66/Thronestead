// Project Name: Thronestead©
// File Name: messages.js
// Version 6.15.2025.20.12
// Developer: Codex
// Unified Messaging System — Inbox + View + Compose + Enhancements

import { supabase } from './supabaseClient.js';
import { escapeHTML, formatDate, fragmentFrom, sanitizeHTML } from './utils.js';
import { authFetchJson } from './fetchJson.js';

let currentSession;
let allMessages = [];
let currentList = [];
let currentPage = 1;
const pageSize = 20;

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
    const filtered = allMessages.filter(m =>
      m.subject?.toLowerCase().includes(query) ||
      m.message?.toLowerCase().includes(query)
    );
    currentPage = 1;
    renderMessages(filtered);
  });

  const prev = document.getElementById('prev-page');
  const next = document.getElementById('next-page');
  if (prev) prev.addEventListener('click', () => changePage(-1));
  if (next) next.addEventListener('click', () => changePage(1));
}

async function loadInbox(session) {
  const container = document.getElementById("message-list");
  container.innerHTML = "<p>Loading messages...</p>";
  try {
    const { messages = [] } = await authFetchJson('/api/messages/inbox', session);
    allMessages = messages;
    currentPage = 1;
    renderMessages(allMessages);
  } catch (err) {
    console.error("❌ Error loading inbox:", err);
    container.innerHTML = "<p>Failed to load messages.</p>";
  }
}

/**
 * Render inbox page of messages with pagination.
 * @param {Array} list Message list to display
 */
function renderMessages(list) {
  currentList = list;
  const container = document.getElementById('message-list');
  const totalPages = Math.ceil(list.length / pageSize);
  if (currentPage > totalPages) currentPage = totalPages || 1;
  document.getElementById('message-count').textContent = `${list.length} Messages`;
  if (!list.length) {
    container.textContent = 'No messages found.';
    updatePagination(totalPages);
    return;
  }
  const start = (currentPage - 1) * pageSize;
  const frag = fragmentFrom(list.slice(start, start + pageSize), msg => {
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
    return card;
  });
  container.replaceChildren(frag);
  updatePagination(totalPages);
}

async function loadMessageView(messageId, session) {
  const container = document.getElementById("message-container");
  container.innerHTML = "<p>Loading message...</p>";

  try {
    const data = await authFetchJson(`/api/messages/${messageId}`, session);

    container.innerHTML = `
      <div class="message-meta">
        <strong>From:</strong> ${escapeHTML(data.username || "Unknown")}<br>
        <strong>Date:</strong> ${formatDate(data.sent_at)}
      </div>
      <h3>${escapeHTML(data.subject || '')}</h3>
      <div class="message-body">${formatIcons(sanitizeHTML(marked.parse(data.message || '')))}</div>
      <div class="message-actions">
        <a href="compose.html?reply_to=${data.user_id}" class="action-btn">Reply</a>
        <button class="action-btn" id="delete-message">Delete</button>
        <button class="action-btn" id="report-message">Report</button>
      </div>`;

    document.getElementById("delete-message").addEventListener("click", async () => {
      if (!confirm("Are you sure you want to delete this message?")) return;
      await authFetchJson('/api/messages/delete', session, {
        method: 'POST',
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
      await authFetchJson('/api/messages/send', session, {
        method: 'POST',
        body: JSON.stringify({ recipient, subject, content, category, sender_id: session.user.id })
      });
      alert("Message sent!");
      window.location.href = "messages.html";
    } catch (err) {
      console.error("❌ Error sending message:", err);
      alert("Failed to send message.");
    }
  });
}


/**
 * Replace emoji codes with image icons.
 * @param {string} html HTML string
 * @returns {string}
 */
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
  currentPage = 1;
  renderMessages(filtered);
}

async function markAllRead() {
  await authFetchJson('/api/messages/mark_all_read', currentSession, { method: 'POST' });
}

function changePage(delta) {
  const total = Math.ceil(currentList.length / pageSize);
  currentPage = Math.min(Math.max(1, currentPage + delta), total || 1);
  renderMessages(currentList);
}

function updatePagination(totalPages) {
  const info = document.getElementById('page-info');
  const prev = document.getElementById('prev-page');
  const next = document.getElementById('next-page');
  if (!info || !prev || !next) return;
  info.textContent = `Page ${currentPage} of ${totalPages || 1}`;
  prev.disabled = currentPage <= 1;
  next.disabled = currentPage >= totalPages;
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
        await authFetchJson('/api/messages/delete', currentSession, {
          method: 'POST',
          body: JSON.stringify({ message_id: messageId })
        });
        await loadInbox(currentSession);
      }
    }
    card.classList.remove('swipe-delete');
    startX = null;
  });
}
