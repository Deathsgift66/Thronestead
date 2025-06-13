// Project Name: Kingmakers Rise©
// File Name: alliance_treaties.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

const TREATY_INFO = {
  'NAP': 'Non-Aggression Pact',
  'Trade Pact': 'Allows trading resources',
  'Mutual Defense': 'Allies will defend each other'
};

let treatyChannel;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Logout
  document.getElementById("logout-btn")?.addEventListener("click", async () => {
    await supabase.auth.signOut();
    window.location.href = "index.html";
  });

  await loadTreatyTabs();

  // ✅ Realtime Treaty Sync
  treatyChannel = supabase
    .channel('public:alliance_treaties')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'alliance_treaties'
    }, loadTreatyTabs)
    .subscribe();

  // ✅ New Treaty Creation
  document.getElementById("create-new-treaty")?.addEventListener("click", async () => {
    const treatyType = prompt("Enter treaty type (NAP, Trade Pact, Mutual Defense):");
    const partnerId = prompt("Enter partner alliance ID:");
    if (!treatyType || !partnerId) return;
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch("/api/alliance-treaties/propose", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-User-ID": user.id },
      body: JSON.stringify({
        treaty_type: treatyType,
        partner_alliance_id: parseInt(partnerId, 10)
      })
    });
    const data = await res.json();
    alert(data.status || "Proposal sent.");
    await loadTreatyTabs();
  });

  // ✅ Modal close
  document.querySelector('.modal-close')?.addEventListener('click', closeModal);
  document.getElementById('treaty-modal')?.addEventListener('click', e => {
    if (e.target.id === 'treaty-modal') closeModal();
  });

  window.addEventListener('beforeunload', () => {
    if (treatyChannel) supabase.removeChannel(treatyChannel);
  });
});

// ✅ Close modal
function closeModal() {
  const modal = document.getElementById('treaty-modal');
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
}

async function loadTreatyTabs() {
  const container = document.getElementById("treaties-container");
  container.innerHTML = "<p>Loading treaties...</p>";

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch("/api/alliance-treaties/my-treaties", {
      headers: { "X-User-ID": user.id }
    });
    const { treaties = [] } = await res.json();
    container.innerHTML = "";

    if (!treaties.length) {
      container.innerHTML = "<p>No treaties found.</p>";
      return;
    }

    treaties.forEach(treaty => {
      const card = document.createElement("div");
      card.className = "treaty-card";
      card.innerHTML = `
        <h3>Treaty with ${escapeHTML(treaty.partner_alliance_id)}</h3>
        <p>Type: <strong title="${escapeHTML(TREATY_INFO[treaty.treaty_type] || '')}">${escapeHTML(treaty.treaty_type)}</strong></p>
        <p>Status: <strong>${escapeHTML(treaty.status)}</strong></p>
        <div class="treaty-actions">
          <button class="action-btn view-treaty-btn" data-treaty='${escapeHTML(JSON.stringify(treaty))}'>View</button>
          ${treaty.status === 'proposed' ? `<button class="action-btn accept-btn" data-id="${treaty.treaty_id}">Accept</button>` : ''}
          ${treaty.status !== 'cancelled' ? `<button class="action-btn cancel-btn" data-id="${treaty.treaty_id}">Cancel</button>` : ''}
        </div>
      `;
      container.appendChild(card);
    });

    bindTreatyButtons();

  } catch (err) {
    console.error("❌ Error loading treaties:", err);
    container.innerHTML = "<p>Failed to load treaties.</p>";
  }
}

function bindTreatyButtons() {
  document.querySelectorAll(".view-treaty-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const treaty = JSON.parse(btn.dataset.treaty);
      await viewTreatyDetails(treaty);
    });
  });

  document.querySelectorAll(".accept-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      respondToTreaty(parseInt(btn.dataset.id, 10), 'accept');
    });
  });

  document.querySelectorAll(".cancel-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      respondToTreaty(parseInt(btn.dataset.id, 10), 'cancel');
    });
  });
}

// ✅ View single treaty modal
async function viewTreatyDetails(treaty) {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch(`/api/alliance-treaties/view/${treaty.treaty_id}`, {
      headers: { 'X-User-ID': user.id }
    });
    const data = await res.json();

    const details = document.getElementById('treaty-details');
    details.innerHTML = `
      <h3>Treaty with Alliance ${escapeHTML(data.partner_alliance_id)}</h3>
      <p>Type: <strong title="${escapeHTML(TREATY_INFO[data.treaty_type] || '')}">${escapeHTML(data.treaty_type)}</strong></p>
      <p>Status: <strong>${escapeHTML(data.status)}</strong></p>
      <p>Signed: ${data.signed_at ? escapeHTML(data.signed_at) : 'Pending'}</p>
    `;

    const modal = document.getElementById('treaty-modal');
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    modal.querySelector('.modal-close')?.focus();
  } catch (err) {
    console.error("❌ Failed to view treaty:", err);
    alert("Could not load treaty details.");
  }
}

// ✅ Accept or Cancel Treaty
async function respondToTreaty(treatyId, action) {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/alliance-treaties/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
      body: JSON.stringify({ treaty_id: treatyId, action })
    });
    const result = await res.json();
    alert(result.status || `Treaty ${action}ed.`);
    await loadTreatyTabs();
  } catch (err) {
    console.error(`❌ Treaty ${action} failed:`, err);
    alert(`Failed to ${action} treaty.`);
  }
}

// ✅ Safe text rendering
function escapeHTML(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
