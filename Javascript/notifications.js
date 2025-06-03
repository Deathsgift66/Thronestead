// notifications.js — FINAL AAA/SSS VERSION — 6.2.25
// Dynamic Notifications Hub — FINAL architecture

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load
  await loadNotifications();

  // ✅ Bind toolbar buttons
  bindToolbar();
});

// ✅ Load Notifications
async function loadNotifications() {
  const container = document.getElementById("notification-feed");

  container.innerHTML = "<p>Loading notifications...</p>";

  try {
    const res = await fetch("/api/notifications/list");
    const data = await res.json();

    container.innerHTML = "";

    if (!data.notifications || data.notifications.length === 0) {
      container.innerHTML = "<p>No notifications found.</p>";
      return;
    }

    data.notifications.forEach(notification => {
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

  } catch (err) {
    console.error("❌ Error loading notifications:", err);
    container.innerHTML = "<p>Failed to load notifications.</p>";
  }
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

// ✅ Mark single notification read
async function markNotificationRead(notificationId) {
  try {
    const res = await fetch("/api/notifications/mark_read", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notification_id: notificationId })
    });

    const result = await res.json();

    if (!res.ok) {
      throw new Error(result.error || "Failed to mark notification as read.");
    }

    console.log("✅ Notification marked as read:", notificationId);

  } catch (err) {
    console.error("❌ Error marking notification as read:", err);
    alert("Failed to mark notification as read.");
  }
}

// ✅ Mark All Read
async function markAllRead() {
  try {
    const res = await fetch("/api/notifications/mark_all_read", {
      method: "POST"
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
      method: "POST"
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
