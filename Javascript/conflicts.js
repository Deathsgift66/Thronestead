/*
Project Name: Kingmakers Rise Frontend
File Name: conflicts.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Hardened Conflicts Page — Matches Conflicts HTML — Tabular View

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
  setupTabs();
  await loadActiveConflicts();
  await loadHistoricalConflicts();
});

// ✅ Setup Tabs
function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");

      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanels.forEach(panel => panel.classList.add("hidden"));

      btn.classList.add("active");
      document.getElementById(targetId).classList.remove("hidden");
    });
  });
}

// ✅ Load Active Conflicts
async function loadActiveConflicts() {
  const tbody = document.getElementById("activeConflictsBody");

  tbody.innerHTML = `
    <tr><td colspan="4">Loading active conflicts...</td></tr>
  `;

  try {
    const res = await fetch("/api/conflicts/active");
    const data = await res.json();

    tbody.innerHTML = "";

    if (!data.conflicts || data.conflicts.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="4">No active conflicts.</td></tr>
      `;
      return;
    }

    data.conflicts.forEach(conflict => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${escapeHTML(conflict.parties || "Unknown")}</td>
        <td>${escapeHTML(conflict.type || "Unknown")}</td>
        <td>${escapeHTML(conflict.status || "Ongoing")}</td>
        <td>${escapeHTML(conflict.started || "Unknown")}</td>
      `;

      tbody.appendChild(row);
    });

  } catch (err) {
    console.error("❌ Error loading active conflicts:", err);
    tbody.innerHTML = `
      <tr><td colspan="4">Failed to load active conflicts.</td></tr>
    `;
  }
}

// ✅ Load Historical Conflicts
async function loadHistoricalConflicts() {
  const tbody = document.getElementById("historicalConflictsBody");

  tbody.innerHTML = `
    <tr><td colspan="5">Loading historical conflicts...</td></tr>
  `;

  try {
    const res = await fetch("/api/conflicts/historical");
    const data = await res.json();

    tbody.innerHTML = "";

    if (!data.conflicts || data.conflicts.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="5">No historical conflicts.</td></tr>
      `;
      return;
    }

    data.conflicts.forEach(conflict => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${escapeHTML(conflict.parties || "Unknown")}</td>
        <td>${escapeHTML(conflict.type || "Unknown")}</td>
        <td>${escapeHTML(conflict.outcome || "Unknown")}</td>
        <td>${escapeHTML(conflict.ended || "Unknown")}</td>
        <td>${escapeHTML(conflict.summary || "No summary.")}</td>
      `;

      tbody.appendChild(row);
    });

  } catch (err) {
    console.error("❌ Error loading historical conflicts:", err);
    tbody.innerHTML = `
      <tr><td colspan="5">Failed to load historical conflicts.</td></tr>
    `;
  }
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
