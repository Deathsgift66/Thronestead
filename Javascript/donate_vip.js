// Comment
// Project Name: Thronestead©
// File Name: donate_vip.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
import { supabase } from "../supabaseClient.js";
import { escapeHTML } from './utils.js';
import { authHeaders } from './auth.js';

// Static token packages purchasable on this page
const TOKEN_PACKAGES = [
  { package_id: 1, name: '1 Token', price_usd: 3.99, tokens: 1 },
  { package_id: 2, name: '3 Tokens', price_usd: 9.99, tokens: 3 },
];

// Redeemable perks mapped by ID
const REDEEM_OPTIONS = [
  {
    perk_id: 'vip1',
    name: 'VIP 1',
    cost: 1,
    details: ['Gold username', 'VIP chat badge', 'Custom troop names']
  },
  {
    perk_id: 'vip2',
    name: 'VIP 2',
    cost: 2,
    details: [
      'All VIP1 perks',
      'Custom troop image',
      'VIP vault skin',
      'Founder badge if subscribed 6+ months'
    ]
  }
];

let tokenPackages = [];
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

  await Promise.all([
    loadPlayerVIPStatus(),
    loadTokenPackages(),
    loadTokenBalance(),
    loadLeaderboard()
  ]);
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
export async function loadPlayerVIPStatus() {
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

// Backwards compatibility export
export { loadPlayerVIPStatus as loadVIPStatus };

export async function loadTokenBalance() {
  try {
    const res = await fetch('/api/tokens/balance', { headers: await authHeaders() });
    if (!res.ok) throw new Error('balance');
    const data = await res.json();
    const banner = document.getElementById('token-balance-banner');
    if (banner) banner.textContent = `${data.tokens} Token${data.tokens === 1 ? '' : 's'} available`;
  } catch {
    const banner = document.getElementById('token-balance-banner');
    if (banner) banner.textContent = 'Tokens unavailable';
  }
}

function renderStatus(status) {
  const banner = document.getElementById('current-status-banner');
  const badge = document.getElementById('founder-preview');

  if (!banner) return;

  if (status.vip_level) {
    banner.innerHTML = `\u{1F396}\uFE0F Your Status: <strong>VIP ${status.vip_level}</strong> \u2014 Active until ${new Date(status.expires_at).toLocaleDateString()}`;
  } else {
    banner.innerHTML = `\u{1F9D9} You are not currently a VIP.`;
  }

  if (status.founder) {
    badge.innerHTML = `\u{1F451} Founder Badge Active`;
    badge.hidden = false;
  } else {
    badge.hidden = true;
  }
}

// ------------------------------
// Token Package Loader and Renderer
// ------------------------------
export async function loadTokenPackages() {
  tokenPackages = TOKEN_PACKAGES;
  renderPackages(tokenPackages);
  renderRedeemables(REDEEM_OPTIONS);
}

function renderPackages(packs) {
  const container = document.getElementById("token-package-cards");
  if (!container) return;
  container.innerHTML = "";

  packs.forEach(pack => {
    const card = document.createElement('div');
    card.className = 'vip-card';
    card.innerHTML = `
      <h3>${escapeHTML(pack.name)}</h3>
      <p>$${pack.price_usd.toFixed(2)}</p>
      <button onclick="selectPackage(${pack.package_id})" class="vip-button">Select</button>
    `;
    container.appendChild(card);
  });
}

function renderRedeemables(options) {
  const container = document.getElementById('redeem-cards');
  if (!container) return;
  container.innerHTML = '';

  options.forEach(perk => {
    const card = document.createElement('div');
    card.className = 'vip-card';
    card.innerHTML = `
      <h3>${escapeHTML(perk.name)}</h3>
      <p>${perk.cost} Token${perk.cost > 1 ? 's' : ''}</p>
      <ul>${perk.details.map(p => `<li>${escapeHTML(p)}</li>`).join('')}</ul>
      <button onclick="redeemPerk('${perk.perk_id}')" class="vip-button">Redeem</button>
    `;
    container.appendChild(card);
  });
}

// Triggered when a package card is selected
export function selectPackage(packId) {
  document.getElementById('selected-tier-id').value = packId;
  document.getElementById('donation-form').hidden = false;
}

// ------------------------------
// Donation Submission
// ------------------------------
function bindDonationForm() {
  const form = document.getElementById("donation-form");
  if (!form) return;

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const packageId = parseInt(document.getElementById("selected-tier-id").value);
    if (!packageId) return alert("Please select a package.");
    await purchaseTokens(packageId);
  });
}

export async function purchaseTokens(package_id) {
  try {
    const res = await fetch("/api/tokens/buy", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(await authHeaders())
      },
      body: JSON.stringify({ package_id })
    });

    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "Donation failed");

    await loadTokenBalance();
    document.getElementById("donation-form").hidden = true;
    alert("Tokens added!");
  } catch (err) {
    console.error("Donation failed", err);
    alert("Donation failed. Please try again.");
  }
}

export async function redeemPerk(perk_id) {
  try {
    const res = await fetch('/api/tokens/redeem', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(await authHeaders())
      },
      body: JSON.stringify({ perk_id })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || 'Redeem failed');
    await Promise.all([loadPlayerVIPStatus(), loadTokenBalance()]);
    alert('Perk redeemed!');
  } catch (err) {
    console.error('Redeem failed', err);
    alert('Redeem failed.');
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
    const res = await fetch("/api/vip/leaderboard", {
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

