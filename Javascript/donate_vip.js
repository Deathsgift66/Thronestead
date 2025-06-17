// Project Name: Thronestead©
// File Name: donate_vip.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from "./supabaseClient.js";
import { escapeHTML } from './utils.js';
import { authHeaders } from './auth.js';
let vipTiers = [];
let vipChannel = null;

// ------------------------------
// DOM Ready Handler
// ------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  await Promise.all([loadVIPStatus(), loadVIPTiers(), loadLeaderboard()]);
  setupRealtimeChannel();
  bindDonationForm();
});

window.addEventListener("beforeunload", () => {
  if (vipChannel) supabase.removeChannel(vipChannel);
});

// ------------------------------
// Real-time Leaderboard Refresh
// ------------------------------
function setupRealtimeChannel() {
  vipChannel = supabase
    .channel("public:vip_donations")
    .on("postgres_changes", { event: "*", schema: "public", table: "vip_donations" }, () => {
      loadLeaderboard();
    })
    .subscribe();
}

// ------------------------------
// VIP Status Renderer
// ------------------------------
export async function loadVIPStatus() {
  try {
    const res = await fetch("/api/vip/status", {
      headers: await authHeaders()
    });
    if (!res.ok) throw new Error("Failed to fetch VIP status");
    const status = await res.json();
    renderStatus(status);
  } catch (err) {
    console.warn("VIP status unavailable", err);
  }
}

function renderStatus(status) {
  const banner = document.getElementById("current-status-banner");
  const founder = document.getElementById("founder-preview");

  if (!banner) return;

  if (status.founder) {
    founder.hidden = false;
    founder.textContent = "Founder Perk Active";
    banner.textContent = "Founder VIP - Permanent";
  } else if (status.vip_level) {
    banner.innerHTML = `VIP ${status.vip_level} - expires in <span id="vip-timer"></span>`;
    renderTimer(status.expires_at);
  } else {
    founder.hidden = true;
    banner.textContent = "No active VIP status";
  }
}

// ------------------------------
// VIP Tier Loader and Renderer
// ------------------------------
export async function loadVIPTiers() {
  try {
    const res = await fetch("/api/vip/tiers", {
      headers: await authHeaders()
    });
    if (!res.ok) throw new Error("Failed to fetch tiers");
    const { tiers } = await res.json();
    vipTiers = tiers || [];
    renderTiers(vipTiers);
  } catch (err) {
    console.warn("No tiers found", err);
    vipTiers = [];
  }
}

function renderTiers(tiers) {
  const container = document.getElementById("vip-tier-cards");
  if (!container) return;
  container.innerHTML = "";

  tiers.forEach(t => {
    const card = document.createElement("div");
    card.className = "vip-tier-card";
    card.innerHTML = `
      <h3>${escapeHTML(t.tier_name)}</h3>
      <div class="vip-price">${t.price_gold} gold</div>
      <button class="vip-button" data-tier="${t.tier_id}">Donate</button>
    `;
    card.querySelector("button").addEventListener("click", () => {
      document.getElementById("selected-tier-id").value = t.tier_id;
      document.getElementById("donation-form").hidden = false;
      renderPerks(t);
    });
    container.appendChild(card);
  });
}

// ------------------------------
// Donation Submission
// ------------------------------
function bindDonationForm() {
  const form = document.getElementById("donation-form");
  if (!form) return;

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const tierId = parseInt(document.getElementById("selected-tier-id").value);
    if (!tierId) return alert("Please select a tier.");
    await submitVIPDonation(tierId);
  });
}

export async function submitVIPDonation(tier_id) {
  try {
    const res = await fetch("/api/vip/donate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(await authHeaders())
      },
      body: JSON.stringify({ tier_id })
    });

    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "Donation failed");

    await loadVIPStatus();
    document.getElementById("donation-form").hidden = true;
    alert("VIP status updated!");
  } catch (err) {
    console.error("Donation failed", err);
    alert("Donation failed. Please try again.");
  }
}

// ------------------------------
// Perks and Countdown Timer
// ------------------------------
export function renderPerks(tier) {
  const container = document.getElementById("founder-preview");
  if (container) container.innerHTML = tier.perks || "No perks listed.";
}

export function renderTimer(expiry) {
  const timerEl = document.getElementById("vip-timer");
  if (!timerEl || !expiry) return;

  function update() {
    const remaining = new Date(expiry) - new Date();
    if (remaining <= 0) {
      timerEl.textContent = "expired";
      clearInterval(interval);
      return;
    }
    const d = Math.floor(remaining / 86400000);
    const h = Math.floor((remaining % 86400000) / 3600000);
    const m = Math.floor((remaining % 3600000) / 60000);
    const s = Math.floor((remaining % 60000) / 1000);
    timerEl.textContent = `${d}d ${h}h ${m}m ${s}s`;
  }

  update();
  const interval = setInterval(update, 1000);
}

// ------------------------------
// Leaderboard Loader and Renderer
// ------------------------------
export async function loadLeaderboard() {
  const table = document.getElementById("leaderboard-body");
  if (!table) return;
  table.innerHTML = "<tr><td colspan='3'>Loading...</td></tr>";

  try {
    const res = await fetch("/api/vip/leaders", {
      headers: await authHeaders()
    });
    const { leaders = [] } = await res.json();
    renderLeaderboard(leaders);
  } catch (err) {
    console.error("Leaderboard error", err);
    table.innerHTML = "<tr><td colspan='3'>Error loading leaderboard</td></tr>";
  }
}

function renderLeaderboard(leaders) {
  const table = document.getElementById("leaderboard-body");
  if (!table) return;
  table.innerHTML = "";

  if (leaders.length === 0) {
    table.innerHTML = "<tr><td colspan='3'>No donations yet.</td></tr>";
    return;
  }

  leaders.forEach((l, idx) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${idx + 1}</td>
      <td>${escapeHTML(l.username)}</td>
      <td>${l.total_donated}</td>
    `;
    table.appendChild(row);
  });
}

// ------------------------------
// Utilities
// ------------------------------
// authHeaders imported from auth.js

