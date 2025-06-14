// Project Name: Kingmakers Rise©
// File Name: audit_log.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// Hardened Admin Audit Log Page — with Supabase auth, loading, error handling, and formatting
import { escapeHTML } from './utils.js';

import { supabase } from './supabaseClient.js';
let eventSource;

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

  const form = document.getElementById("audit-filter-form");
  if (form) {
    form.addEventListener("submit", async e => {
      e.preventDefault();
      await loadAuditLog();
    });
  }

  // ✅ Initial load
  await loadAuditLog();

  // ✅ Real-time updates via SSE
  try {
    eventSource = new EventSource('/api/admin/audit-log/stream');
    eventSource.onmessage = (ev) => {
      const log = JSON.parse(ev.data);
      prependLogRow(log);
    };
  } catch (err) {
    console.error('SSE connection failed', err);
  }
  window.addEventListener('beforeunload', () => {
    if (eventSource) eventSource.close();
  });
});

// ✅ Load Audit Log
async function loadAuditLog() {
  const tbody = document.getElementById("audit-log-body");
  const user = document.getElementById("filter-user")?.value.trim();
  const action = document.getElementById("filter-action")?.value.trim();
  const from = document.getElementById("filter-from")?.value;
  const to = document.getElementById("filter-to")?.value;
  const limit = document.getElementById("filter-limit")?.value || 100;

  // Show loading state
  tbody.innerHTML = `
    <tr><td colspan="4">Loading audit log...</td></tr>
  `;

  try {
    const params = new URLSearchParams();
    if (user) params.append("user_id", user);
    if (action) params.append("action", action);
    if (from) params.append("date_from", from);
    if (to) params.append("date_to", to);
    if (limit) params.append("limit", limit);

    const res = await fetch(`/api/admin/audit-log?${params.toString()}`);
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
        <td>${formatTimestamp(log.created_at)}</td>
        <td>${escapeHTML(log.action)}</td>
        <td>${escapeHTML(log.user_id || '')}</td>
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

function prependLogRow(log) {
  const tbody = document.getElementById('audit-log-body');
  const row = document.createElement('tr');
  row.innerHTML = `
    <td>${formatTimestamp(log.created_at)}</td>
    <td>${escapeHTML(log.action)}</td>
    <td>${escapeHTML(log.user_id || '')}</td>
    <td>${escapeHTML(log.details)}</td>
  `;
  tbody.prepend(row);
  if (tbody.children.length > 100) {
    tbody.removeChild(tbody.lastChild);
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
