// Project Name: Kingmakers Rise©
// File Name: player_management.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML, fragmentFrom } from './utils.js';

let playerChannel;

document.addEventListener("DOMContentLoaded", async () => {
  await loadPlayerTable();

  document.getElementById("search-button")?.addEventListener("click", loadPlayerTable);
  document.getElementById("search-reset")?.addEventListener("click", () => {
    const input = document.getElementById("search-input");
    if (input) input.value = "";
    loadPlayerTable();
  });

  const bulkActions = {
    "bulk-ban": "ban",
    "bulk-flag": "flag",
    "bulk-logout": "logout",
    "bulk-reset-password": "reset_password"
  };

  Object.entries(bulkActions).forEach(([btnId, action]) => {
    document.getElementById(btnId)?.addEventListener("click", () => handleBulkAction(action));
  });

  document.getElementById("modal-close-btn")?.addEventListener("click", () =>
    document.getElementById("admin-modal")?.classList.add("hidden")
  );

  // ✅ Supabase real-time channel
  playerChannel = supabase
    .channel('players')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'users' }, loadPlayerTable)
    .subscribe();
});

window.addEventListener('beforeunload', () => {
  if (playerChannel) playerChannel.unsubscribe();
});

// ✅ Load Player Table
/**
 * Fetch and render the player table based on current search query.
 * Utilizes a document fragment to minimize reflow when inserting rows.
 */
async function loadPlayerTable() {
  const tableBody = document.querySelector("#player-table tbody");
  const query = document.getElementById("search-input")?.value.trim() || "";
  tableBody.innerHTML = "<tr><td colspan='8'>Loading players...</td></tr>";

  try {
    const res = await fetch(`/api/admin/players?search=${encodeURIComponent(query)}`);
    const { players } = await res.json();

    tableBody.innerHTML = players?.length
      ? ''
      : "<tr><td colspan='8'>No players found.</td></tr>";

    const rows = fragmentFrom(players, player => {
      const row = document.createElement('tr');
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
      return row;
    });
    tableBody.appendChild(rows);

    rebindActionButtons();

  } catch (err) {
    console.error("❌ Error loading player table:", err);
    tableBody.innerHTML = "<tr><td colspan='8'>Failed to load players.</td></tr>";
  }
}

function rebindActionButtons() {
  const bindAction = (selector, actionName) => {
    document.querySelectorAll(selector).forEach(btn =>
      btn.addEventListener("click", () => showModalConfirm(`${capitalize(actionName)} Player`, btn.dataset.id, actionName))
    );
  };

  bindAction(".flag-btn", "flag");
  bindAction(".freeze-btn", "freeze");
  bindAction(".ban-btn", "ban");
  bindAction(".history-btn", "history");
}

// ✅ Handle Bulk Action
async function handleBulkAction(action) {
  const selected = Array.from(document.querySelectorAll(".player-select:checked")).map(cb => cb.dataset.id);
  if (!selected.length) return alert("Please select at least one player.");
  if (!confirm(`Perform "${action}" on ${selected.length} players?`)) return;

  try {
    const res = await fetch("/api/admin/bulk_action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, player_ids: selected })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Bulk action failed.");

    alert(result.message || `Bulk "${action}" completed.`);
    await loadPlayerTable();
  } catch (err) {
    console.error(`❌ Bulk ${action} failed:`, err);
    alert(`Failed to perform "${action}".`);
  }
}

// ✅ Show Modal Confirmation
async function showModalConfirm(title, userId, action) {
  const modal = document.getElementById("admin-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalBody = document.getElementById("modal-body");
  const confirmBtn = document.getElementById("modal-confirm-btn");

  modalTitle.textContent = title;
  modalBody.innerHTML = `Are you sure you want to <strong>${escapeHTML(action)}</strong> player ID <strong>${escapeHTML(userId)}</strong>?`;

  modal.classList.remove("hidden");

  const newConfirmBtn = confirmBtn.cloneNode(true);
  confirmBtn.replaceWith(newConfirmBtn);

  newConfirmBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/admin/player_action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, player_id: userId })
      });

      const result = await res.json();
      if (!res.ok) throw new Error(result.error || "Action failed.");

      alert(result.message || `Action "${action}" completed.`);
      modal.classList.add("hidden");
      await loadPlayerTable();
    } catch (err) {
      console.error(`❌ ${action} failed:`, err);
      alert(`Failed to ${action}.`);
    }
  });
}

// ✅ Escape HTML

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
