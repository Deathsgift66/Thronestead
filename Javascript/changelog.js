// changelog.js — FINAL AAA/SSS VERSION — 6.2.25
// Hardened Changelog Page — Clean version history display

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "login.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load
  await loadChangelog();
});

// ✅ Load Changelog Entries
async function loadChangelog() {
  const container = document.getElementById("changelog-entries");

  container.innerHTML = "<p>Loading changelog...</p>";

  try {
    const res = await fetch("/api/changelog");
    const data = await res.json();

    container.innerHTML = "";

    if (!data.entries || data.entries.length === 0) {
      container.innerHTML = "<p>No changelog entries available.</p>";
      return;
    }

    data.entries.forEach(entry => {
      const entryDiv = document.createElement("div");
      entryDiv.classList.add("changelog-entry");

      // Format version header
      const versionHeader = document.createElement("h3");
      versionHeader.textContent = `Version ${escapeHTML(entry.version)} — ${formatDate(entry.date)}`;

      // Format changes list
      const ul = document.createElement("ul");
      if (Array.isArray(entry.changes)) {
        entry.changes.forEach(change => {
          const li = document.createElement("li");
          li.textContent = change;
          ul.appendChild(li);
        });
      } else {
        const li = document.createElement("li");
        li.textContent = "No changes listed.";
        ul.appendChild(li);
      }

      // Assemble entry
      entryDiv.appendChild(versionHeader);
      entryDiv.appendChild(ul);
      container.appendChild(entryDiv);
    });

  } catch (err) {
    console.error("❌ Error loading changelog:", err);
    container.innerHTML = "<p>Failed to load changelog.</p>";
  }
}

// ✅ Format Date (YYYY-MM-DD → MM/DD/YYYY)
function formatDate(dateStr) {
  if (!dateStr) return "Unknown";
  const date = new Date(dateStr);
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
