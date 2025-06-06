/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_treaties.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Modern Card-Based Alliance Treaties Center

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

  // ✅ Initial load
  await loadTreaties();

  // ✅ Bind "Create New Treaty" button
  const createBtn = document.getElementById("create-new-treaty");
  if (createBtn) {
    createBtn.addEventListener("click", async () => {
      const treatyType = prompt("Enter treaty type (e.g., NAP, Trade Pact, Mutual Defense):");
      if (!treatyType) return;
      const res = await fetch("/api/alliance-treaties/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: treatyType })
      });
      const data = await res.json();
      alert(data.message || "Treaty created.");
      await loadTreaties();
    });
  }
});

// ✅ Load Alliance Treaties
async function loadTreaties() {
  const container = document.getElementById("treaties-container");
  container.innerHTML = "<p>Loading treaties...</p>";

  try {
    const res = await fetch("/api/alliance-treaties");
    const data = await res.json();

    container.innerHTML = "";

    if (!data.treaties || data.treaties.length === 0) {
      container.innerHTML = "<p>No treaties found.</p>";
      return;
    }

    data.treaties.forEach(treaty => {
      const card = document.createElement("div");
      card.classList.add("treaty-card");

      card.innerHTML = `
        <h3>${treaty.alliance_name}</h3>
        <p>Type: <strong>${treaty.type}</strong></p>
        <p>Status: <strong>${treaty.status}</strong></p>
        <div class="treaty-actions">
          <button class="action-btn view-treaty-btn" data-treaty='${JSON.stringify(treaty)}'>View</button>
        </div>
      `;

      container.appendChild(card);
    });

    // Add View button listeners
    document.querySelectorAll(".view-treaty-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const treaty = JSON.parse(btn.dataset.treaty);
        viewTreatyDetails(treaty);
      });
    });

  } catch (err) {
    console.error("❌ Error loading treaties:", err);
    container.innerHTML = "<p>Failed to load treaties.</p>";
  }
}

// ✅ View Treaty Details (Modal or Navigate)
function viewTreatyDetails(treaty) {
  // For now, just an alert — you can replace with a modal
  alert(`Treaty with ${treaty.alliance_name}\nType: ${treaty.type}\nStatus: ${treaty.status}\n\n(Modal coming soon!)`);

  // Example: To open a modal in future
  // const modal = document.getElementById("treaty-modal");
  // Populate modal fields...
  // modal.classList.add("open");
}
