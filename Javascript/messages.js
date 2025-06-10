/*
Project Name: Kingmakers Rise Frontend
File Name: messages.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Unified Messaging System — Inbox + View + Compose

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  const { user } = session;
  const accessToken = session.access_token;

  // ✅ Determine page
  if (document.getElementById("message-list")) {
    await loadInbox(user, accessToken);
    subscribeToMessages(user.id, () => loadInbox(user, accessToken));
  } else if (document.getElementById("message-container")) {
    const urlParams = new URLSearchParams(window.location.search);
    const messageId = urlParams.get("message_id");
    if (messageId) {
      await loadMessageView(messageId, user, accessToken);
      subscribeToMessages(user.id, (payload) => {
        if (payload.new.message_id === parseInt(messageId)) {
          loadMessageView(messageId, user, accessToken);
        }
      });
    } else {
      document.getElementById("message-container").innerHTML = "<p>Invalid message.</p>";
    }
  } else if (document.getElementById("compose-form")) {
    setupCompose(user, accessToken);
  }
});

// ✅ Load Inbox
async function loadInbox(user, token) {
  const container = document.getElementById("message-list");
  container.innerHTML = "<p>Loading messages...</p>";

  try {
    const res = await fetch('/api/messages/list', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-User-ID': user.id
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');

    container.innerHTML = "";

    if (!data.messages || data.messages.length === 0) {
      container.innerHTML = "<p>No messages found.</p>";
      return;
    }

    data.messages.forEach(msg => {
      const card = document.createElement("div");
      card.classList.add("message-card");

      card.innerHTML = `
        <a href="message.html?message_id=${msg.message_id}">
          <div class="message-meta">
            <span>From: ${escapeHTML(msg.username || "Unknown")}</span>
            <span>${formatDate(msg.sent_at)}</span>
          </div>
          <div class="message-subject">${escapeHTML((msg.subject || msg.message).substring(0, 50))}</div>
        </a>
      `;

      container.appendChild(card);
    });

  } catch (err) {
    console.error("❌ Error loading inbox:", err);
    container.innerHTML = "<p>Failed to load messages.</p>";
  }
}

// ✅ Load Message View
async function loadMessageView(messageId, user, token) {
  const container = document.getElementById("message-container");
  container.innerHTML = "<p>Loading message...</p>";

  try {
    const res = await fetch(`/api/messages/${messageId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-User-ID': user.id
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
        ${escapeHTML(data.message)}
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
            'Authorization': `Bearer ${token}`,
            'X-User-ID': user.id
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
function setupCompose(user, token) {
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

    if (!recipient || !messageContent) {
      alert("Please enter both recipient and message.");
      return;
    }

    try {
      const res = await fetch('/api/messages/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-User-ID': user.id
        },
        body: JSON.stringify({ recipient, subject, content: messageContent })
      });
      if (!res.ok) throw new Error();

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

// ✅ Real-time subscription
function subscribeToMessages(userId, callback) {
  supabase
    .channel('messages:' + userId)
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'player_messages', filter: `recipient_id=eq.${userId}` },
      payload => callback(payload)
    )
    .subscribe();
}
