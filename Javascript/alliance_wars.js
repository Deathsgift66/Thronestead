/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_wars.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Modern Card-Based Alliance Wars Board — Matches alliance_wars.html perfectly

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Initial load
  await loadCustomBoard();
  await loadAllianceWars();
});

// ✅ Load Alliance Custom Board (image + text)
async function loadCustomBoard() {
  try {
    const res = await fetch("/api/alliance-wars/custom-board");
    const data = await res.json();

    const imgSlot = document.getElementById("custom-image-slot");
    const textSlot = document.getElementById("custom-text-slot");

    imgSlot.innerHTML = data.image_url
      ? `<img src="${data.image_url}" alt="Alliance War Banner" class="war-board-image">`
      : "<p>No custom image set.</p>";

    textSlot.innerHTML = data.custom_text
      ? `<p>${data.custom_text}</p>`
      : "<p>No custom text set.</p>";

  } catch (err) {
    console.error("❌ Error loading custom board:", err);
    document.getElementById("custom-image-slot").innerHTML = "<p>Error loading image.</p>";
    document.getElementById("custom-text-slot").innerHTML = "<p>Error loading text.</p>";
  }
}

// ✅ Load Alliance Wars
async function loadAllianceWars() {
  const container = document.getElementById("wars-container");
  container.innerHTML = "<p>Loading alliance wars...</p>";

  try {
    const res = await fetch("/api/alliance-wars");
    const data = await res.json();

    container.innerHTML = "";

    // Render Active Wars
    if (data.active_wars && data.active_wars.length > 0) {
      const activeHeader = document.createElement("h3");
      activeHeader.textContent = "⚔️ Active Wars";
      container.appendChild(activeHeader);

      data.active_wars.forEach(war => {
        const card = document.createElement("div");
        card.classList.add("war-card");

        card.innerHTML = `
          <h4>${war.opponent}</h4>
          <p>Type: <strong>${war.type}</strong></p>
          <p>Status: <strong>${war.status}</strong></p>
          <p>Started: <strong>${war.started}</strong></p>
          <p>Turns Left: <strong>${war.turns_left}</strong></p>
          <div class="war-actions">
            <button class="action-btn view-war-btn" data-war='${JSON.stringify(war)}'>View</button>
          </div>
        `;

        container.appendChild(card);
      });
    } else {
      const noActive = document.createElement("p");
      noActive.textContent = "No active wars.";
      container.appendChild(noActive);
    }

    // Render Past Wars
    if (data.past_wars && data.past_wars.length > 0) {
      const pastHeader = document.createElement("h3");
      pastHeader.textContent = "🏅 Past Wars";
      container.appendChild(pastHeader);

      data.past_wars.forEach(war => {
        const card = document.createElement("div");
        card.classList.add("war-card");

        card.innerHTML = `
          <h4>${war.opponent}</h4>
          <p>Result: <strong>${war.result}</strong></p>
          <p>Ended: <strong>${war.ended}</strong></p>
          <div class="war-actions">
            <button class="action-btn view-war-btn" data-war='${JSON.stringify(war)}'>View</button>
          </div>
        `;

        container.appendChild(card);
      });
    } else {
      const noPast = document.createElement("p");
      noPast.textContent = "No past wars.";
      container.appendChild(noPast);
    }

    // Add View button listeners
    document.querySelectorAll(".view-war-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const war = JSON.parse(btn.dataset.war);
        viewWarDetails(war);
      });
    });

  } catch (err) {
    console.error("❌ Error loading alliance wars:", err);
    container.innerHTML = "<p>Failed to load alliance wars.</p>";
  }
}

// ✅ View War Details (Modal or Navigate)
function viewWarDetails(war) {
  // For now: simple alert (can replace with modal or navigation)
  alert(`War vs ${war.opponent}\nType: ${war.type || "N/A"}\nStatus: ${war.status || war.result}\n\n(More details available in future updates)`);

  // Example for modal:
  // const modal = document.getElementById("war-modal");
  // Populate modal fields...
  // modal.classList.add("open");

  // Example for page nav:
  // window.location.href = `/alliance_war_detail.html?war_id=${war.id}`;
}
