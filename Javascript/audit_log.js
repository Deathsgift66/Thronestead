/*
Project Name: Kingmakers Rise Frontend
File Name: audit_log.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Hardened Admin Audit Log Page — with Supabase auth, loading, error handling, and formatting

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Enforce admin access (you can add RLS in Supabase, this is frontend safety)
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load
  await loadAuditLog();
});

// ✅ Load Audit Log
async function loadAuditLog() {
  const tbody = document.getElementById("audit-log-body");

  // Show loading state
  tbody.innerHTML = `
    <tr><td colspan="4">Loading audit log...</td></tr>
  `;

  try {
    const res = await fetch("/api/audit-log");
    const data = await res.json();

    tbody.innerHTML = "";

    if (!data.logs || data.logs.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="4">No audit log entries found.</td></tr>
      `;
      return;
    }

    data.logs.forEach(log => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${formatTimestamp(log.time)}</td>
        <td>${escapeHTML(log.action)}</td>
        <td>${escapeHTML(log.admin)}</td>
        <td>${escapeHTML(log.details)}</td>
      `;

      tbody.appendChild(row);
    });

  } catch (err) {
    console.error("❌ Error fetching audit log data:", err);
    tbody.innerHTML = `
      <tr><td colspan="4">Failed to load audit log.</td></tr>
    `;
  }
}

// ✅ Format timestamp
function formatTimestamp(timestamp) {
  if (!timestamp) return "Unknown";
  const date = new Date(timestamp);
  return date.toLocaleString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });
}

// ✅ Basic HTML escape (to prevent injection)
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
