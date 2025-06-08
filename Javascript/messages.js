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

  // ✅ Determine page
  if (document.getElementById("message-list")) {
    // Inbox page
    await loadInbox();
  } else if (document.getElementById("message-container")) {
    // Message view page
    const urlParams = new URLSearchParams(window.location.search);
    const messageId = urlParams.get("message_id");
    if (messageId) {
      await loadMessageView(messageId);
    } else {
      document.getElementById("message-container").innerHTML = "<p>Invalid message.</p>";
    }
  } else if (document.getElementById("compose-form")) {
    // Compose page
    setupCompose();
  }
});

// ✅ Load Inbox
async function loadInbox() {
  const container = document.getElementById("message-list");
  container.innerHTML = "<p>Loading messages...</p>";

  try {
    const { data: { user } } = await supabase.auth.getUser();

    // ✅ JOIN with users table for sender name
    const { data, error } = await supabase
      .from("player_messages")
      .select("message_id, subject, message, sent_at, is_read, users(username)")
      .eq("recipient_id", user.id)
      .eq("deleted_by_recipient", false)
      .order("sent_at", { ascending: false })
      .limit(100);

    if (error) throw error;

    container.innerHTML = "";

    if (!data || data.length === 0) {
      container.innerHTML = "<p>No messages found.</p>";
      return;
    }

    data.forEach(msg => {
      const card = document.createElement("div");
      card.classList.add("message-card");

      card.innerHTML = `
        <a href="message.html?message_id=${msg.message_id}">
          <div class="message-meta">
            <span>From: ${escapeHTML(msg.users?.username || "Unknown")}</span>
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
async function loadMessageView(messageId) {
  const container = document.getElementById("message-container");
  container.innerHTML = "<p>Loading message...</p>";

  try {
    const { data: { user } } = await supabase.auth.getUser();

    // ✅ JOIN with users table for sender name
    const { data, error } = await supabase
      .from("player_messages")
      .select("message_id, subject, message, sent_at, is_read, user_id, deleted_by_recipient, users(username)")
      .eq("message_id", messageId)
      .eq("recipient_id", user.id)
      .single();

    if (error || !data) {
      throw new Error("Message not found or access denied.");
    }

    // ✅ Mark as read
    await supabase
      .from("player_messages")
      .update({ is_read: true })
      .eq("message_id", messageId);

    container.innerHTML = `
      <div class="message-meta">
        <strong>From:</strong> ${escapeHTML(data.users?.username || "Unknown")}
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
        const { error: deleteError } = await supabase
          .from("player_messages")
          .update({ deleted_by_recipient: true })
          .eq("message_id", messageId)
          .eq("recipient_id", user.id);

        if (deleteError) throw deleteError;

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
function setupCompose() {
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
      const { data: { user } } = await supabase.auth.getUser();

      // ✅ Look up recipient user_id
      const { data: recipientData, error: recipientError } = await supabase
        .from("users")
        .select("user_id")
        .eq("username", recipient)
        .single();

      if (recipientError || !recipientData) {
        throw new Error("Recipient not found.");
      }

      const { error: sendError } = await supabase
        .from("player_messages")
        .insert({
          recipient_id: recipientData.user_id,
          user_id: user.id,
          subject: subject || null,
          message: messageContent,
          sent_at: new Date().toISOString(),
          is_read: false
        });

      if (sendError) throw sendError;

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
