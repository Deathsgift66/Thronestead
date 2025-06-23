// Project Name: Thronestead©
// File Name: black_market.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { showToast, escapeHTML } from './utils.js';
import { authHeaders, getAuth } from './auth.js';

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
  document.getElementById('closeModal')?.addEventListener('click', closeModal);
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

  if (sort === 'price') filtered.sort((a, b) => a.price_per_unit - b.price_per_unit);
  if (sort === 'quantity') filtered.sort((a, b) => b.stock_remaining - a.stock_remaining);
  if (sort === 'expiry') filtered.sort((a, b) => new Date(a.expires_at) - new Date(b.expires_at));

  const grid = document.getElementById('listingsGrid');
  grid.innerHTML = '';

  filtered.forEach(listing => {
    const card = document.createElement('div');
    card.className = 'listing-card';
    const expiresIn = formatExpiry(listing.expires_at);
    card.innerHTML = `
      <h4>${escapeHTML(listing.item_name)}</h4>
      <p>${escapeHTML(listing.description)}</p>
      <p><strong>Price:</strong> ${listing.price_per_unit} ${listing.currency_type}</p>
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
  document.getElementById('modalPrice').textContent = `${listing.price_per_unit} ${listing.currency_type} each`;

  const qtyInput = document.getElementById('purchaseQty');
  qtyInput.value = 1;
  qtyInput.max = listing.stock_remaining;
  document.getElementById('purchaseModal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('purchaseModal').classList.add('hidden');
  currentListing = null;
}

async function confirmPurchase() {
  const qty = parseInt(document.getElementById('purchaseQty').value, 10);
  if (!currentListing || !qty || qty < 1 || qty > currentListing.stock_remaining) return;

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
    closeModal();
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
      div.textContent = `${t.item_name} x${t.quantity} @ ${t.price_per_unit} ${t.currency_type}`;
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



