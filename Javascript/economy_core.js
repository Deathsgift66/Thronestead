// Consolidated economy modules (buildings, market, black market, VIP)
// market.js and black_market_routes.js were not found in this repository

// Consolidated economy-related modules
import { supabase } from '../supabaseClient.js';
import { showToast, escapeHTML, openModal, closeModal } from './core_utils.js';
import { authHeaders, getAuth } from './auth.js';

// ===== buildings.js =====

document.addEventListener('DOMContentLoaded', async () => {
  await loadVillages();
  setupEventListeners();
});

// Fetch and populate the village selector dropdown
async function loadVillages() {
  try {
    const res = await fetch('/api/kingdom/villages');
    const json = await res.json();
    const villages = json.villages || json;
    const select = document.getElementById('villageSelect');
    select.innerHTML = '';

    villages.forEach(village => {
      const option = document.createElement('option');
      option.value = village.village_id;
      option.textContent = village.village_name;
      select.appendChild(option);
    });

    if (villages.length > 0) {
      loadBuildings(villages[0].village_id);
    }

    select.addEventListener('change', e => {
      loadBuildings(e.target.value);
    });
  } catch (err) {
    console.error('Failed to load villages:', err);
    alert('Error loading villages. Try again later.');
  }
}

// Load buildings for a specific village
async function loadBuildings(villageId) {
  const tbody = document.getElementById('buildingsTableBody');
  tbody.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';
  try {
    const res = await fetch(`/api/buildings/village/${villageId}`);
    const json = await res.json();
    const buildings = json.buildings || json;
    tbody.innerHTML = '';

    buildings.forEach(building => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><img src="Assets/buildings/${building.icon}" alt="${building.name}" width="32" height="32" onerror="this.src='Assets/buildings/placeholder.png'"></td>
        <td>${building.name}</td>
        <td>${building.level}</td>
        <td>${building.status}</td>
        <td>
          <button class="info-btn" data-id="${building.id}">📘 Info</button>
          <button class="upgrade-btn" data-id="${building.id}" ${building.status == 'Upgrading' ? 'disabled' : ''}>⬆ Upgrade</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    attachRowActions();
  } catch (err) {
    console.error('Failed to load buildings:', err);
    tbody.innerHTML = '<tr><td colspan="5">Error loading buildings.</td></tr>';
    alert('Error loading buildings. Try again later.');
  }
}

// Attach modal and upgrade button logic
function attachRowActions() {
  document.querySelectorAll('.info-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      const buildingId = e.target.dataset.id;
      try {
        const res = await fetch(`/api/buildings/info/${buildingId}`);
        const data = await res.json();
        const info = data.building || data;

        document.getElementById('modalBuildingName').textContent = escapeHTML(info.building_name || info.name);
        document.getElementById('modalBuildingDesc').textContent = escapeHTML(info.description || '');
        document.getElementById('modalBuildCost').textContent = formatCost(info.upgrade_cost);

        document.getElementById('buildingModal').classList.remove('hidden');
      } catch (err) {
        console.error('Failed to fetch building info:', err);
        alert('Error fetching building info.');
      }
    });
  });

  document.querySelectorAll('.upgrade-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      const buildingId = e.target.dataset.id;
      const villageId = document.getElementById('villageSelect').value;
      try {
        const res = await fetch(`/api/buildings/upgrade`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            village_id: parseInt(villageId),
            building_id: parseInt(buildingId)
          })
        });
        const result = await res.json();
        alert(result.message || 'Upgrade started!');
        loadBuildings(document.getElementById('villageSelect').value);
      } catch (err) {
        console.error('Upgrade failed:', err);
        alert('Failed to start upgrade. Try again later.');
      }
    });
  });
}

// Format upgrade cost nicely for the modal
function formatCost(costObj) {
  if (!costObj) return '';
  return Object.entries(costObj)
    .map(([resource, amount]) => `${resource}: ${amount}`)
    .join('\n');
}

// Setup modal close button
function setupEventListeners() {
  const closeBtn = document.getElementById('buildingModalClose');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      document.getElementById('buildingModal').classList.add('hidden');
    });
  }
}
\n// ===== black_market.js =====
let listings = [];
let kingdomId = null;
let userId = null;
let currentListing = null;

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }


  await initUserSession();
  await loadListings();
  await loadHistory();

  document.getElementById('searchInput')?.addEventListener('input', renderListings);
  document.getElementById('sortSelect')?.addEventListener('change', renderListings);
  document.getElementById('closeModal')?.addEventListener('click', closePurchaseModal);
  document.getElementById('confirmPurchase')?.addEventListener('click', confirmPurchase);
  document.getElementById('createListingBtn')?.addEventListener('click', openCreateModal);

  // Real-time refresh
  setInterval(loadListings, 15000);
  setInterval(loadHistory, 30000);
});

// ========== USER INIT ==========
async function initUserSession() {
  const { user } = await getAuth();
  userId = user.id;

  const { data: profile } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', userId)
    .single();

  if (!profile?.kingdom_id) {
    alert("You must be in a kingdom to use the Black Market.");
    return;
  }

  kingdomId = profile.kingdom_id;

  const { data: resources } = await supabase
    .from('kingdom_resources')
    .select('*')
    .eq('kingdom_id', kingdomId)
    .single();

  if (resources) {
    document.getElementById('resourceDisplay').textContent =
      `${resources.gold} Gold • ${resources.gems} Gems`;
  }
}

// ========== LISTINGS ==========
async function loadListings() {
  try {
    const res = await fetch('/api/black_market/listings', { headers: await authHeaders() });
    const data = await res.json();
    listings = data.listings || [];
    renderListings();
    document.getElementById('lastUpdated').textContent =
      `Updated: ${new Date().toLocaleTimeString()}`;
  } catch (e) {
    showToast("Failed to load listings.");
    console.error("Listings error:", e);
  }
}

function renderListings() {
  const query = document.getElementById('searchInput')?.value.toLowerCase() || '';
  const sort = document.getElementById('sortSelect')?.value || '';
  let filtered = listings.filter(l => l.item_name.toLowerCase().includes(query));

  if (sort === 'price') filtered.sort((a, b) => (a.price_per_unit || 0) - (b.price_per_unit || 0));
  if (sort === 'quantity') filtered.sort((a, b) => b.stock_remaining - a.stock_remaining);
  if (sort === 'expiry') filtered.sort((a, b) => new Date(a.expires_at) - new Date(b.expires_at));

  const grid = document.getElementById('listingsGrid');
  grid.innerHTML = '';

  if (filtered.length === 0) {
    grid.innerHTML = '<p>No listings found.</p>';
    return;
  }

  filtered.forEach(listing => {
    const card = document.createElement('div');
    card.className = 'listing-card';
    const expiresIn = formatExpiry(listing.expires_at);
    card.innerHTML = `
      <h4>${escapeHTML(listing.item_name)}</h4>
      <p>${escapeHTML(listing.description)}</p>
      <p><strong>Price:</strong> ${listing.price_per_unit} ${listing.currency_type || 'Unknown Currency'}</p>
      <p><strong>Qty:</strong> ${listing.stock_remaining}</p>
      <p><small>${expiresIn}</small></p>
      <button class="btn">Buy</button>
    `;
    card.querySelector('button').addEventListener('click', (e) => {
      e.stopPropagation();
      openPurchaseModal(listing);
    });
    grid.appendChild(card);
  });
}

// ========== PURCHASE ==========
function openPurchaseModal(listing) {
  currentListing = listing;
  document.getElementById('modalTitle').textContent = listing.item_name;
  document.getElementById('modalDesc').textContent = listing.description;
  document.getElementById('modalPrice').textContent = `${listing.price_per_unit} ${listing.currency_type || 'Unknown Currency'} each`;

  const qtyInput = document.getElementById('purchaseQty');
  qtyInput.value = 1;
  qtyInput.max = listing.stock_remaining;
  openModal('purchaseModal');
}

function closePurchaseModal() {
  closeModal('purchaseModal');
  currentListing = null;
}

async function confirmPurchase() {
  const qty = parseInt(document.getElementById('purchaseQty').value, 10);
  if (!currentListing || !qty || qty < 1 || qty > currentListing.stock_remaining) return;
  if (currentListing.price_per_unit <= 0) {
    showToast('Invalid price for this listing.');
    return;
  }

  try {
    await fetch('/api/black_market/purchase', {
      method: 'POST',
      headers: {
        ...(await authHeaders()),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        listing_id: currentListing.id,
        quantity: qty,
        kingdom_id: kingdomId
      })
    });
    showToast(`✅ Purchased ${qty} ${currentListing.item_name}`);
    closePurchaseModal();
    await loadListings();
    await loadHistory();
    await initUserSession();
  } catch (e) {
    showToast("❌ Purchase failed.");
    console.error("Purchase error:", e);
  }
}

// ========== HISTORY ==========
async function loadHistory() {
  try {
    const res = await fetch(`/api/black_market/history?kingdom_id=${kingdomId}`, { headers: await authHeaders() });
    const data = await res.json();
    const container = document.getElementById('purchaseHistory');
    container.innerHTML = '';
    (data.trades || []).forEach(t => {
      const div = document.createElement('div');
      div.className = 'history-item';
      div.textContent = `${t.item_name} x${t.quantity} @ ${t.price_per_unit} ${t.currency_type || 'Unknown Currency'}`;
      container.appendChild(div);
    });
  } catch (e) {
    console.warn("History load failed:", e);
  }
}

// ========== CREATE LISTING (Future Use) ==========
function openCreateModal() {
  // Hook for seller listing form in the future
  alert("Listing creation is not yet available. Coming soon!");
}

// ========== UTILS ==========
function formatExpiry(expiry) {
  const now = new Date();
  const exp = new Date(expiry);
  const diffMs = exp - now;
  if (diffMs < 0) return 'Expired';
  const mins = Math.floor(diffMs / 60000);
  const hrs = Math.floor(mins / 60);
  return `${hrs}h ${mins % 60}m left`;
}

\n// ===== donate_vip.js =====
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
    type: 'Cosmetic',
    description: 'Gold username and chat badge',
    details: ['Gold username', 'VIP chat badge', 'Custom troop names']
  },
  {
    perk_id: 'vip2',
    name: 'VIP 2',
    cost: 2,
    type: 'Cosmetic',
    description: 'Extra cosmetics and founder badge',
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
    renderTimer(status.expires_at);
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
    card.dataset.packageId = pack.package_id;
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
    card.setAttribute('data-bs-toggle', 'tooltip');
    card.title = perk.details.join(', ');
    card.innerHTML = `
      <h3>${escapeHTML(perk.name)}</h3>
      <p>${perk.cost} Token${perk.cost > 1 ? 's' : ''}</p>
      <p class="perk-type">${escapeHTML(perk.type)}</p>
      <p class="perk-desc">${escapeHTML(perk.description)}</p>
      <button onclick="redeemPerk('${perk.perk_id}')" class="vip-button">Redeem</button>
    `;
    container.appendChild(card);
    if (window.bootstrap) new window.bootstrap.Tooltip(card);
  });
}

// Triggered when a package card is selected
export function selectPackage(packId) {
  const container = document.getElementById('token-package-cards');
  if (container) {
    container.querySelectorAll('.vip-card').forEach(card => {
      card.classList.toggle('selected', card.dataset.packageId == packId);
    });
  }
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

// Expose functions for inline handlers
window.selectPackage = selectPackage;
window.redeemPerk = redeemPerk;
window.purchaseTokens = purchaseTokens;



