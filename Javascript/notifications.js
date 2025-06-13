/*
Project Name: Kingmakers Rise Frontend
File Name: notifications.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let currentSession;
let notificationChannel;
let allNotifications = [];

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  currentSession = session;

  await loadNotifications();

  notificationChannel = supabase
    .channel(`notifications-${session.user.id}`)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'notifications',
      filter: `user_id=eq.${session.user.id}`
    }, async () => {
      await loadNotifications();
    })
    .subscribe();

  const filterInput = document.getElementById('notification-filter');
  if (filterInput) {
    filterInput.addEventListener('input', filterNotifications);
  }

  bindToolbar();
});

window.addEventListener('beforeunload', () => {
  if (notificationChannel) supabase.removeChannel(notificationChannel);
});

// ✅ Load Notifications
async function loadNotifications() {
  const container = document.getElementById("notification-feed");

  container.innerHTML = "<p>Loading notifications...</p>";

  try {
    const res = await fetch("/api/notifications/list", {
      headers: {
        'Authorization': `Bearer ${currentSession.access_token}`,
        'X-User-ID': currentSession.user.id
      }
    });
    const data = await res.json();

    container.innerHTML = "";

    allNotifications = data.notifications || [];
    renderNotifications(allNotifications);

  } catch (err) {
    console.error("❌ Error loading notifications:", err);
    container.innerHTML = "<p>Failed to load notifications.</p>";
  }
}

function renderNotifications(list) {
  const container = document.getElementById("notification-feed");

  container.innerHTML = "";

  if (!list || list.length === 0) {
    container.innerHTML = "<p>No notifications found.</p>";
    return;
  }

  list.forEach(notification => {
      const card = document.createElement("div");
      card.classList.add("notification-item");

      card.innerHTML = `
        <div class="meta">
          <strong>${escapeHTML(notification.title)}</strong> 
          — [${escapeHTML(notification.category)} | ${escapeHTML(notification.priority)}] 
          — ${formatDate(notification.created_at)}
        </div>
        <div class="message">
          ${escapeHTML(notification.message)}
        </div>
        <div class="notification-actions">
          ${notification.link_action ? `<a href="${escapeHTML(notification.link_action)}" class="action-btn">View</a>` : ""}
          <button class="action-btn mark-read-btn" data-id="${notification.notification_id}">Mark Read</button>
        </div>
      `;

      container.appendChild(card);
    });

    // ✅ Bind individual Mark Read buttons
    document.querySelectorAll(".mark-read-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const notificationId = btn.dataset.id;
        await markNotificationRead(notificationId);
        await loadNotifications();
      });
    });

}

// ✅ Bind Toolbar
function bindToolbar() {
  const buttons = document.querySelectorAll(".royal-button");

  buttons.forEach(btn => {
    const text = btn.textContent.trim();

    if (text === "Mark All Read") {
      btn.addEventListener("click", async () => {
        if (!confirm("Mark all notifications as read?")) return;
        await markAllRead();
        await loadNotifications();
      });
    } else if (text === "Clear All") {
      btn.addEventListener("click", async () => {
        if (!confirm("Clear all notifications? This cannot be undone.")) return;
        await clearAllNotifications();
        await loadNotifications();
      });
    }
  });
}

function filterNotifications() {
  const input = document.getElementById('notification-filter');
  if (!input) return;
  const term = input.value.toLowerCase();
  const filtered = allNotifications.filter(n =>
    n.title.toLowerCase().includes(term) || n.message.toLowerCase().includes(term)
  );
  renderNotifications(filtered);
}

// ✅ Mark single notification read
async function markNotificationRead(notificationId) {
  try {
    const res = await fetch("/api/notifications/mark_read", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'Authorization': `Bearer ${currentSession.access_token}`,
        'X-User-ID': currentSession.user.id
      },
      body: JSON.stringify({ notification_id: notificationId })
    });

    const result = await res.json();

    if (!res.ok) {
      throw new Error(result.error || "Failed to mark notification as read.");
    }


  } catch (err) {
    console.error("❌ Error marking notification as read:", err);
    alert("Failed to mark notification as read.");
  }
}

// ✅ Mark All Read
async function markAllRead() {
  try {
    const res = await fetch("/api/notifications/mark_all_read", {
      method: "POST",
      headers: {
        'Authorization': `Bearer ${currentSession.access_token}`,
        'X-User-ID': currentSession.user.id
      }
    });

    const result = await res.json();

    if (!res.ok) {
      throw new Error(result.error || "Failed to mark all as read.");
    }

    alert("All notifications marked as read.");

  } catch (err) {
    console.error("❌ Error marking all read:", err);
    alert("Failed to mark all as read.");
  }
}

// ✅ Clear All
async function clearAllNotifications() {
  try {
    const res = await fetch("/api/notifications/clear_all", {
      method: "POST",
      headers: {
        'Authorization': `Bearer ${currentSession.access_token}`,
        'X-User-ID': currentSession.user.id
      }
    });

    const result = await res.json();

    if (!res.ok) {
      throw new Error(result.error || "Failed to clear all notifications.");
    }

    alert("All notifications cleared.");

  } catch (err) {
    console.error("❌ Error clearing notifications:", err);
    alert("Failed to clear notifications.");
  }
}

// ✅ Date formatting
function formatDate(ts) {
  if (!ts) return "Unknown";
  const date = new Date(ts);
  return date.toLocaleDateString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit"
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
