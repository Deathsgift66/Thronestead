/*
Project Name: Kingmakers Rise Frontend
File Name: player_management.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let playerChannel;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Rely on authGuard.js — no duplicate session checks needed
  // ✅ Initial load
  await loadPlayerTable();

  // ✅ Bind filter search button
  document.getElementById("search-button").addEventListener("click", async () => {
    await loadPlayerTable();
  });
  document.getElementById("search-reset").addEventListener("click", async () => {
    document.getElementById("search-input").value = "";
    await loadPlayerTable();
  });

  // ✅ Bind bulk actions
  document.getElementById("bulk-ban").addEventListener("click", async () => {
    await handleBulkAction("ban");
  });
  document.getElementById("bulk-flag").addEventListener("click", async () => {
    await handleBulkAction("flag");
  });
  document.getElementById("bulk-logout").addEventListener("click", async () => {
    await handleBulkAction("logout");
  });
  document.getElementById("bulk-reset-password").addEventListener("click", async () => {
    await handleBulkAction("reset_password");
  });

  // ✅ Bind modal close
  document.getElementById("modal-close-btn").addEventListener("click", () => {
    document.getElementById("admin-modal").classList.add("hidden");
  });

  // ✅ Real-time updates
  playerChannel = supabase
    .channel('players')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'users' }, async () => {
      await loadPlayerTable();
    })
    .subscribe();
});

window.addEventListener('beforeunload', () => {
  if (playerChannel) {
    playerChannel.unsubscribe();
  }
});

// ✅ Load Player Table
async function loadPlayerTable() {
  const tableBody = document.querySelector("#player-table tbody");
  const query = document.getElementById("search-input").value.trim();

  tableBody.innerHTML = "<tr><td colspan='8'>Loading players...</td></tr>";

  try {
    const res = await fetch(`/api/admin/players?search=${encodeURIComponent(query)}`);
    const data = await res.json();

    tableBody.innerHTML = "";

    if (!data.players || data.players.length === 0) {
      tableBody.innerHTML = "<tr><td colspan='8'>No players found.</td></tr>";
      return;
    }

    data.players.forEach(player => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td><input type="checkbox" class="player-select" data-id="${player.user_id}"></td>
        <td>${escapeHTML(player.user_id)}</td>
        <td>${escapeHTML(player.username)}</td>
        <td>${escapeHTML(player.email)}</td>
        <td>${escapeHTML(player.kingdom_name)}</td>
        <td>${escapeHTML(player.vip_tier)}</td>
        <td>${escapeHTML(player.status)}</td>
        <td>
          <button class="action-btn flag-btn" data-id="${player.user_id}">Flag</button>
          <button class="action-btn freeze-btn" data-id="${player.user_id}">Freeze</button>
          <button class="action-btn ban-btn" data-id="${player.user_id}">Ban</button>
          <button class="action-btn history-btn" data-id="${player.user_id}">History</button>
        </td>
      `;

      tableBody.appendChild(row);
    });

    // ✅ Bind action buttons
    document.querySelectorAll(".flag-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        await showModalConfirm("Flag Player", btn.dataset.id, "flag");
      });
    });

    document.querySelectorAll(".freeze-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        await showModalConfirm("Freeze Player", btn.dataset.id, "freeze");
      });
    });

    document.querySelectorAll(".ban-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        await showModalConfirm("Ban Player", btn.dataset.id, "ban");
      });
    });

    document.querySelectorAll(".history-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        await showModalConfirm("View Player History", btn.dataset.id, "history");
      });
    });

  } catch (err) {
    console.error("❌ Error loading player table:", err);
    tableBody.innerHTML = "<tr><td colspan='8'>Failed to load players.</td></tr>";
  }
}

// ✅ Handle Bulk Action
async function handleBulkAction(action) {
  const selected = Array.from(document.querySelectorAll(".player-select:checked")).map(cb => cb.dataset.id);

  if (selected.length === 0) {
    alert("Please select at least one player.");
    return;
  }

  if (!confirm(`Perform "${action}" on ${selected.length} players?`)) return;

  try {
    const res = await fetch("/api/admin/bulk_action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        player_ids: selected
      })
    });

    const result = await res.json();

    if (!res.ok) {
      throw new Error(result.error || "Bulk action failed.");
    }

    alert(result.message || `Bulk action "${action}" completed.`);
    await loadPlayerTable();

  } catch (err) {
    console.error(`❌ Error performing bulk ${action}:`, err);
    alert(`Failed to perform bulk ${action}.`);
  }
}

// ✅ Show Modal Confirmation
async function showModalConfirm(title, userId, action) {
  const modal = document.getElementById("admin-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalBody = document.getElementById("modal-body");
  const confirmBtn = document.getElementById("modal-confirm-btn");

  modalTitle.textContent = title;
  modalBody.innerHTML = `Are you sure you want to perform "<strong>${action}</strong>" on player ID: <strong>${escapeHTML(userId)}</strong>?`;

  modal.classList.remove("hidden");

  // ✅ Clean previous listener
  confirmBtn.replaceWith(confirmBtn.cloneNode(true));
  const newConfirmBtn = document.getElementById("modal-confirm-btn");

  newConfirmBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/admin/player_action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          player_id: userId
        })
      });

      const result = await res.json();

      if (!res.ok) {
        throw new Error(result.error || "Action failed.");
      }

      alert(result.message || `Action "${action}" completed.`);
      modal.classList.add("hidden");
      await loadPlayerTable();

    } catch (err) {
      console.error(`❌ Error performing ${action}:`, err);
      alert(`Failed to perform "${action}".`);
    }
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
