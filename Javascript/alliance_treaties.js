/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_treaties.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Modern Card-Based Alliance Treaties Center

import { supabase } from './supabaseClient.js';

const TREATY_INFO = {
  'NAP': 'Non-Aggression Pact',
  'Trade Pact': 'Allows trading resources',
  'Mutual Defense': 'Allies will defend each other'
};

let treatyChannel;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  await loadTreatyTabs();

  treatyChannel = supabase
    .channel('public:alliance_treaties')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'alliance_treaties' }, async () => {
      await loadTreatyTabs();
    })
    .subscribe();

  // ✅ Bind "Create New Treaty" button
  const createBtn = document.getElementById("create-new-treaty");
  if (createBtn) {
    createBtn.addEventListener("click", async () => {
      const treatyType = prompt("Enter treaty type (e.g., NAP, Trade Pact, Mutual Defense):");
      const partnerId = prompt("Enter partner alliance id:");
      if (!treatyType || !partnerId) return;
      const { data: { user } } = await supabase.auth.getUser();
      const res = await fetch("/api/alliance-treaties/propose", {
        method: "POST",
        headers: { "Content-Type": "application/json", 'X-User-ID': user.id },
        body: JSON.stringify({ treaty_type: treatyType, partner_alliance_id: parseInt(partnerId, 10) })
      });
      const data = await res.json();
      alert(data.status || "Proposal sent.");
      await loadTreatyTabs();
    });
  }
});

window.addEventListener('beforeunload', () => {
  if (treatyChannel) supabase.removeChannel(treatyChannel);
});

async function loadTreatyTabs() {
  const container = document.getElementById("treaties-container");
  container.innerHTML = "<p>Loading treaties...</p>";

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch("/api/alliance-treaties/my-treaties", { headers: { 'X-User-ID': user.id } });
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
        <h3>Treaty with ${escapeHTML(treaty.partner_alliance_id)}</h3>
        <p>Type: <strong title="${escapeHTML(TREATY_INFO[treaty.treaty_type] || '')}">${escapeHTML(treaty.treaty_type)}</strong></p>
        <p>Status: <strong>${escapeHTML(treaty.status)}</strong></p>
        <div class="treaty-actions">
          <button class="action-btn view-treaty-btn" data-treaty='${JSON.stringify(treaty)}'>View</button>
          ${treaty.status === 'proposed' ? `<button class="action-btn accept-btn" data-id="${treaty.treaty_id}">Accept</button>` : ''}
          ${treaty.status !== 'cancelled' ? `<button class="action-btn cancel-btn" data-id="${treaty.treaty_id}">Cancel</button>` : ''}
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
    document.querySelectorAll(".accept-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        await respondToTreaty(parseInt(btn.dataset.id, 10), 'accept');
      });
    });
    document.querySelectorAll(".cancel-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        await respondToTreaty(parseInt(btn.dataset.id, 10), 'cancel');
      });
    });

  } catch (err) {
    console.error("❌ Error loading treaties:", err);
    container.innerHTML = "<p>Failed to load treaties.</p>";
  }
}

// ✅ View Treaty Details (Modal or Navigate)
async function viewTreatyDetails(treaty) {
  const { data: { user } } = await supabase.auth.getUser();
  const res = await fetch(`/api/alliance-treaties/view/${treaty.treaty_id}`, { headers: { 'X-User-ID': user.id } });
  const data = await res.json();
  const modal = document.getElementById('treaty-modal');
  const details = document.getElementById('treaty-details');
  details.innerHTML = `
    <h3>Treaty with Alliance ${escapeHTML(data.partner_alliance_id)}</h3>
    <p>Type: <strong title="${escapeHTML(TREATY_INFO[data.treaty_type] || '')}">${escapeHTML(data.treaty_type)}</strong></p>
    <p>Status: <strong>${escapeHTML(data.status)}</strong></p>
    <p>Signed: ${data.signed_at ? escapeHTML(data.signed_at) : 'Pending'}</p>
  `;
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
  modal.querySelector('.modal-close').focus();
}

document.querySelector('.modal-close')?.addEventListener('click', () => {
  const modal = document.getElementById('treaty-modal');
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
});

document.getElementById('treaty-modal')?.addEventListener('click', e => {
  if (e.target.id === 'treaty-modal') {
    const modal = document.getElementById('treaty-modal');
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
  }
});

async function respondToTreaty(treatyId, action) {
  const { data: { user } } = await supabase.auth.getUser();
  await fetch('/api/alliance-treaties/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
    body: JSON.stringify({ treaty_id: treatyId, action })
  });
  await loadTreatyTabs();
}

// Basic HTML escape helper
function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
