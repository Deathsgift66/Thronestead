/*
Project Name: Kingmakers Rise Frontend
File Name: changelog.js
Updated: 2025-06-13 by Codex
Description: Real-time changelog viewer with Supabase integration, expandable for filters and search.
*/

import { supabase } from './supabaseClient.js';

let realtimeSub;

// ✅ Unified auth header fetch
async function authHeaders() {
  const [{ data: { user } }, { data: { session } }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession()
  ]);
  if (!user || !session) throw new Error('Unauthorized');
  return {
    'X-User-ID': user.id,
    Authorization: `Bearer ${session.access_token}`
  };
}

// ✅ Entry point
document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return window.location.href = "login.html";

  // ✅ Bind logout button
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  await loadChangelog();
  setupRealtime();

  // ✅ Optional refresh button
  document.getElementById('refresh-log')?.addEventListener('click', loadChangelog);
});

// ✅ Load and render all changelog entries
async function loadChangelog() {
  const container = document.getElementById("changelog-entries");
  container.innerHTML = "<p>Loading changelog...</p>";

  try {
    const res = await fetch("/api/changelog", { headers: await authHeaders() });
    const data = await res.json();
    container.innerHTML = "";

    const entries = data.entries || [];
    if (!entries.length) {
      container.innerHTML = "<p>No changelog entries available.</p>";
      return;
    }

    entries.forEach(entry => renderEntry(entry, container));
  } catch (err) {
    console.error("❌ Error loading changelog:", err);
    container.innerHTML = "<p>Failed to load changelog.</p>";
  }
}

// ✅ Format and render a single changelog entry
function renderEntry(entry, container) {
  const entryDiv = document.createElement("div");
  entryDiv.classList.add("changelog-entry");

  const version = document.createElement("h3");
  version.textContent = `Version ${escapeHTML(entry.version)} — ${formatDate(entry.date)}`;
  entryDiv.appendChild(version);

  // Optionally display tags (future use)
  if (entry.tags?.length) {
    const tagSpan = document.createElement("span");
    tagSpan.className = "changelog-tags";
    tagSpan.textContent = entry.tags.join(', ');
    entryDiv.appendChild(tagSpan);
  }

  // Format list of changes
  const list = document.createElement("ul");
  (entry.changes || []).forEach(change => {
    const li = document.createElement("li");
    li.textContent = change;
    list.appendChild(li);
  });

  entryDiv.appendChild(list);
  container.appendChild(entryDiv);
}

// ✅ Set up Supabase real-time subscription for new changelog entries
function setupRealtime() {
  realtimeSub = supabase
    .channel('public:game_changelog')
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'game_changelog'
    }, loadChangelog)
    .subscribe();
}

window.addEventListener('beforeunload', () => {
  realtimeSub?.unsubscribe();
});

// ✅ Format ISO date to locale-friendly string
function formatDate(dateStr) {
  if (!dateStr) return "Unknown";
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit"
  });
}

// ✅ HTML sanitization
function escapeHTML(str) {
  return str
    ? String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;")
    : "";
}
