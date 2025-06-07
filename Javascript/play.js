/*
Project Name: Kingmakers Rise Frontend
File Name: play.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load
  await loadDashboard();
});

// ✅ Load Dashboard Data
async function loadDashboard() {
  const resourceContainer = document.getElementById("resource-overview");
  const identityContainer = document.getElementById("identity-panel");
  const activityContainer = document.getElementById("activity-feed");
  const militaryContainer = document.getElementById("military-panel");

  // Placeholders while loading
  resourceContainer.innerHTML = "<p>Loading resources...</p>";
  identityContainer.innerHTML = "<p>Loading identity...</p>";
  activityContainer.innerHTML = "<p>Loading activity feed...</p>";
  militaryContainer.innerHTML = "<p>Loading military summary...</p>";

  try {
    const res = await fetch("/api/kingdom/overview");
    const data = await res.json();

    // ✅ Resources Panel
    resourceContainer.innerHTML = "";
    if (data.resources && Object.keys(data.resources).length > 0) {
      const list = document.createElement("ul");
      for (const [resource, amount] of Object.entries(data.resources)) {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${escapeHTML(resource)}:</strong> ${amount}`;
        list.appendChild(li);
      }
      resourceContainer.appendChild(list);
    } else {
      resourceContainer.innerHTML = "<p>No resources found.</p>";
    }

    // ✅ Identity Panel
    identityContainer.innerHTML = `
      <p><strong>Kingdom:</strong> ${escapeHTML(data.kingdom_name)}</p>
      <p><strong>Ruler:</strong> ${escapeHTML(data.owner_name)}</p>
      <p><strong>VIP Tier:</strong> ${escapeHTML(data.vip_tier)}</p>
      <p><strong>Morale:</strong> ${data.morale}%</p>
      <p><strong>Region:</strong> ${escapeHTML(data.region)}</p>
    `;

    // ✅ Activity Feed
    activityContainer.innerHTML = "";
    if (data.activity_feed && data.activity_feed.length > 0) {
      const list = document.createElement("ul");
      data.activity_feed.forEach(entry => {
        const li = document.createElement("li");
        li.innerHTML = `
          [${formatDate(entry.timestamp)}] ${escapeHTML(entry.message)}
        `;
        list.appendChild(li);
      });
      activityContainer.appendChild(list);
    } else {
      activityContainer.innerHTML = "<p>No recent activity.</p>";
    }

    // ✅ Military Panel
    militaryContainer.innerHTML = "";
    if (data.military_summary && Object.keys(data.military_summary).length > 0) {
      const list = document.createElement("ul");
      for (const [unit, count] of Object.entries(data.military_summary)) {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${escapeHTML(unit)}:</strong> ${count}`;
        list.appendChild(li);
      }
      militaryContainer.appendChild(list);
    } else {
      militaryContainer.innerHTML = "<p>No military units present.</p>";
    }

  } catch (err) {
    console.error("❌ Error loading dashboard:", err);
    resourceContainer.innerHTML = "<p>Failed to load resources.</p>";
    identityContainer.innerHTML = "<p>Failed to load identity.</p>";
    activityContainer.innerHTML = "<p>Failed to load activity feed.</p>";
    militaryContainer.innerHTML = "<p>Failed to load military summary.</p>";
  }
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
