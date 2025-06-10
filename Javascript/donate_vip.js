/*
Project Name: Kingmakers Rise Frontend
File Name: donate_vip.js
Date: June 2, 2025
Author: Deathsgift66
*/
// VIP Donation Logic

import { supabase } from "./supabaseClient.js";

let vipStatus = null;
let vipTiers = [];
let vipChannel = null;
let currentSession = null;

async function init() {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }
  currentSession = session;

  await loadVIPStatus();
  await loadVIPTiers();
  await loadLeaderboard();

  vipChannel = supabase
    .channel("public:vip_donations")
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "vip_donations" },
      () => {
        loadLeaderboard();
      },
    )
    .subscribe();

  const form = document.getElementById("donation-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const tierId = document.getElementById("selected-tier-id").value;
      if (tierId) {
        await submitVIPDonation(parseInt(tierId));
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", init);

export async function loadVIPStatus() {
  try {
    const headers = {
      Authorization: `Bearer ${currentSession.access_token}`,
      "X-User-ID": currentSession.user.id,
    };
    const res = await fetch("/api/vip/status", { headers });
    if (!res.ok) throw new Error("failed");
    vipStatus = await res.json();
    renderStatus(vipStatus);
  } catch {
    vipStatus = null;
  }
}

export async function loadVIPTiers() {
  try {
    const headers = {
      Authorization: `Bearer ${currentSession.access_token}`,
      "X-User-ID": currentSession.user.id,
    };
    const res = await fetch("/api/vip/tiers", { headers });
    if (!res.ok) throw new Error("failed");
    const data = await res.json();
    vipTiers = data.tiers || [];
    renderTiers(vipTiers);
  } catch {
    vipTiers = [];
  }
}

export async function submitVIPDonation(tier_id) {
  try {
    const res = await fetch("/api/vip/donate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${currentSession.access_token}`,
        "X-User-ID": currentSession.user.id,
      },
      body: JSON.stringify({ tier_id }),
    });
    if (!res.ok) {
      const err = await res.json();
      alert(err.detail || "Failed");
      return;
    }
    await loadVIPStatus();
    document.getElementById("donation-form").hidden = true;
    alert("VIP updated!");
  } catch (err) {
    console.error(err);
  }
}

function renderTiers(tiers) {
  const container = document.getElementById("vip-tier-cards");
  if (!container) return;
  container.innerHTML = "";
  tiers.forEach((t) => {
    const card = document.createElement("div");
    card.className = "vip-tier-card";
    card.innerHTML = `
      <h3>${t.tier_name}</h3>
      <div class="vip-price">${t.price_gold} gold</div>
      <button class="vip-button" data-tier="${t.tier_id}">Donate</button>
    `;
    const btn = card.querySelector("button");
    btn.addEventListener("click", () => {
      document.getElementById("selected-tier-id").value = t.tier_id;
      document.getElementById("donation-form").hidden = false;
      renderPerks(t);
    });
    container.appendChild(card);
  });
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
    banner.textContent = "No active VIP status";
  }
}

export function renderPerks(tier) {
  const container = document.getElementById("founder-preview");
  if (!container) return;
  container.innerHTML = tier.perks || "";
}

export function renderTimer(expiry) {
  const timerEl = document.getElementById("vip-timer");
  if (!timerEl || !expiry) return;
  function update() {
    const diff = new Date(expiry) - new Date();
    if (diff <= 0) {
      timerEl.textContent = "expired";
      clearInterval(interval);
      return;
    }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    timerEl.textContent = `${d}d ${h}h ${m}m ${s}s`;
  }
  update();
  const interval = setInterval(update, 1000);
}

export async function loadLeaderboard() {
  const container = document.getElementById("leaderboard-body");
  if (!container) return;
  container.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';
  try {
    const headers = {
      Authorization: `Bearer ${currentSession.access_token}`,
      "X-User-ID": currentSession.user.id,
    };
    const res = await fetch("/api/vip/leaders", { headers });
    const data = await res.json();
    renderLeaderboard(data.leaders || []);
  } catch (err) {
    console.error(err);
    container.innerHTML =
      '<tr><td colspan="3">Error loading leaderboard</td></tr>';
  }
}

function renderLeaderboard(leaders) {
  const container = document.getElementById("leaderboard-body");
  if (!container) return;
  container.innerHTML = "";
  if (!leaders.length) {
    container.innerHTML = '<tr><td colspan="3">No donations yet.</td></tr>';
    return;
  }
  leaders.forEach((l, idx) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${idx + 1}</td>
      <td>${escapeHTML(l.username)}</td>
      <td>${l.total_donated}</td>
    `;
    container.appendChild(row);
  });
}

function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

window.addEventListener("beforeunload", () => {
  if (vipChannel) supabase.removeChannel(vipChannel);
});
