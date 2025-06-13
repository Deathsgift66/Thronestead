// Project Name: Kingmakers Rise©
// File Name: notifications.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

let currentSession;
let notificationChannel;
let allNotifications = [];

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  currentSession = session;

  await loadNotifications();

  // ✅ Real-time notification updates
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

// ✅ Load Notifications from API
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
    allNotifications = data.notifications || [];

    renderNotifications(allNotifications);
  } catch (err) {
    console.error("❌ Error loading notifications:", err);
    container.innerHTML = "<p>Failed to load notifications.</p>";
  }
}

// ✅ Render Notification Cards
function renderNotifications(list) {
  const container = document.getElementById("notification-feed");
  container.innerHTML = "";

  if (!list || list.length === 0) {
    container.innerHTML = "<p>No notifications found.</p>";
    return;
  }

  // Unread first
  list.sort((a, b) => (a.is_read === b.is_read) ? 0 : a.is_read ? 1 : -1);

  list.forEach(notification => {
    const card = document.createElement("div");
    card.classList.add("notification-item");
    if (!notification.is_read) card.classList.add("unread");

    card.innerHTML = `
      <div class="meta">
        <strong>${escapeHTML(notification.title)}</strong> 
        <span class="pill pill-${notification.priority.toLowerCase()}">${escapeHTML(notification.priority)}</span>
        <span class="pill">${escapeHTML(notification.category)}</span>
        <span class="timestamp">${formatDate(notification.created_at)}</span>
      </div>
      <div class="message">${escapeHTML(notification.message)}</div>
      <div class="notification-actions">
        ${notification.link_action ? `<a href="${escapeHTML(notification.link_action)}" class="action-btn">View</a>` : ""}
        <button class="action-btn mark-read-btn" data-id="${notification.notification_id}">Mark Read</button>
      </div>
    `;

    container.appendChild(card);
  });

  // ✅ Bind Mark Read Buttons
  document.querySelectorAll(".mark-read-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const notificationId = btn.dataset.id;
      await markNotificationRead(notificationId);
      await loadNotifications();
    });
  });
}

// ✅ Filter by keyword
function filterNotifications() {
  const input = document.getElementById('notification-filter');
  const term = input?.value.toLowerCase() || '';
  const filtered = allNotifications.filter(n =>
    n.title.toLowerCase().includes(term) ||
    n.message.toLowerCase().includes(term) ||
    n.category.toLowerCase().includes(term) ||
    n.priority.toLowerCase().includes(term)
  );
  renderNotifications(filtered);
}

// ✅ Bind toolbar buttons
function bindToolbar() {
  const buttons = document.querySelectorAll(".royal-button");
  buttons.forEach(btn => {
    const action = btn.textContent.trim();
    if (action === "Mark All Read") {
      btn.addEventListener("click", async () => {
        if (confirm("Mark all notifications as read?")) {
          await markAllRead();
          await loadNotifications();
        }
      });
    } else if (action === "Clear All") {
      btn.addEventListener("click", async () => {
        if (confirm("Clear all notifications? This cannot be undone.")) {
          await clearAllNotifications();
          await loadNotifications();
        }
      });
    }
  });
}

// ✅ Mark one notification
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
    if (!res.ok) throw new Error(result.error || "Failed");
  } catch (err) {
    console.error("❌ Error marking notification:", err);
    alert("Failed to mark as read.");
  }
}

// ✅ Mark all notifications
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
    if (!res.ok) throw new Error(result.error || "Failed");
    alert("All marked as read.");
  } catch (err) {
    console.error("❌ Error marking all read:", err);
    alert("Failed to mark all read.");
  }
}

// ✅ Delete all notifications
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
    if (!res.ok) throw new Error(result.error || "Failed");
    alert("All notifications cleared.");
  } catch (err) {
    console.error("❌ Error clearing notifications:", err);
    alert("Failed to clear notifications.");
  }
}

// ✅ Format date
function formatDate(ts) {
  if (!ts) return "Unknown";
  const date = new Date(ts);
  return date.toLocaleDateString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit"
  });
}

// ✅ Escape dangerous input
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
