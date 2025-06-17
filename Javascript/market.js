// Project Name: Thronestead©
// File Name: market.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';

let currentUserId = null;
let isAdmin = false;
let realtimeChannel = null;

// ✅ Main Initialization

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Session & Role
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return (window.location.href = "login.html");
  currentUserId = session.user.id;

  const { data: userMeta } = await supabase.from('users').select('is_admin').eq('user_id', currentUserId).single();
  isAdmin = userMeta?.is_admin || false;

  setupTabs();
  setupCreateListingModal();
  subscribeRealtime();
  startAutoRefresh();

  await loadMarketListings();
});

// ✅ Tabs Logic
function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const targetId = btn.getAttribute("data-tab");
      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanels.forEach(panel => panel.classList.add("hidden"));
      btn.classList.add("active");
      document.getElementById(targetId).classList.remove("hidden");

      if (targetId === "market-listings") await loadMarketListings();
      if (targetId === "my-listings") await loadMyListings();
      if (targetId === "trade-history") await loadTradeHistory();
    });
  });
}

// ✅ Modal for Creating New Listings
function setupCreateListingModal() {
  const btn = document.getElementById('open-create-listing');
  const modal = document.getElementById('create-listing-modal');
  const close = document.getElementById('close-create-listing');

  if (btn && modal && close) {
    btn.addEventListener('click', () => modal.classList.remove('hidden'));
    close.addEventListener('click', () => modal.classList.add('hidden'));

    const form = document.getElementById('create-listing-form');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const item = document.getElementById('listing-item').value;
      const qty = parseInt(document.getElementById('listing-qty').value);
      const price = parseInt(document.getElementById('listing-price').value);

      if (!item || qty <= 0 || price <= 0) return alert("Invalid values");

      try {
        const res = await fetch('/api/market/create_listing', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': currentUserId
          },
          body: JSON.stringify({ item_name: item, quantity: qty, price })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to create listing");
        modal.classList.add('hidden');
        alert("Listing created!");
        await loadMyListings();
      } catch (err) {
        console.error("Listing creation error:", err);
        alert(err.message);
      }
    });
  }
}

// ✅ Load Market Listings
async function loadMarketListings() {
  const container = document.getElementById("market-listings");
  container.innerHTML = "<p>Loading market listings...</p>";

  try {
    const res = await fetch("/api/market/listings", {
      headers: { 'X-User-ID': currentUserId }
    });
    const data = await res.json();
    container.innerHTML = "";

    if (!data.listings?.length) {
      return (container.innerHTML = "<p>No listings available.</p>");
    }

    const list = document.createElement("ul");
    data.listings.forEach(l => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${escapeHTML(l.item_name)}</strong> — ${l.quantity} @ ${l.price}g/unit
        <br> Seller: ${escapeHTML(l.seller_name)}
        ${isAdmin ? `<button class='danger-btn' data-id='${l.listing_id}'>Remove</button>` : ''}
      `;
      list.appendChild(li);
    });
    container.appendChild(list);

    if (isAdmin) {
      container.querySelectorAll(".danger-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.id;
          if (confirm("Remove this listing?")) {
            await fetch(`/api/market/admin_remove_listing`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'X-User-ID': currentUserId },
              body: JSON.stringify({ listing_id: id })
            });
            await loadMarketListings();
          }
        });
      });
    }

  } catch (err) {
    console.error("❌ Listing load error:", err);
    container.innerHTML = "<p>Error loading listings.</p>";
  }
  updateLastUpdated();
}

// ✅ Load My Listings
async function loadMyListings() {
  const container = document.getElementById("my-listings");
  container.innerHTML = "<p>Loading...</p>";
  try {
    const res = await fetch("/api/market/my_listings", {
      headers: { 'X-User-ID': currentUserId }
    });
    const data = await res.json();
    container.innerHTML = "";

    if (!data.listings?.length) {
      return (container.innerHTML = "<p>No active listings.</p>");
    }

    const list = document.createElement("ul");
    data.listings.forEach(l => {
      const li = document.createElement("li");
      li.innerHTML = `
        ${escapeHTML(l.item_name)} — ${l.quantity} @ ${l.price}g
        <button class='cancel-btn' data-id='${l.listing_id}'>Cancel</button>`;
      list.appendChild(li);
    });
    container.appendChild(list);

    container.querySelectorAll(".cancel-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.id;
        if (!confirm("Cancel this listing?")) return;
        await fetch("/api/market/cancel_listing", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-ID': currentUserId },
          body: JSON.stringify({ listing_id: id })
        });
        await loadMyListings();
      });
    });
  } catch (err) {
    container.innerHTML = "<p>Failed to load.</p>";
  }
  updateLastUpdated();
}

// ✅ Load Trade History
async function loadTradeHistory() {
  const container = document.getElementById("trade-history");
  container.innerHTML = "<p>Loading...</p>";

  try {
    const res = await fetch("/api/market/history", {
      headers: { 'X-User-ID': currentUserId }
    });
    const data = await res.json();

    if (!data.trades?.length) {
      return (container.innerHTML = "<p>No trades found.</p>");
    }

    const list = document.createElement("ul");
    data.trades.forEach(tr => {
      const li = document.createElement("li");
      li.innerHTML = `
        ${escapeHTML(tr.item_name)} — ${tr.quantity} @ ${tr.price}g
        <br>Buyer: ${escapeHTML(tr.buyer_name)} — Seller: ${escapeHTML(tr.seller_name)}
        <br>Completed: ${formatTimestamp(tr.completed_at)}
      `;
      list.appendChild(li);
    });
    container.innerHTML = "";
    container.appendChild(list);
  } catch (err) {
    container.innerHTML = "<p>Error loading trade history.</p>";
  }
  updateLastUpdated();
}

function subscribeRealtime() {
  realtimeChannel = supabase
    .channel('public:market_listings')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'market_listings' }, loadMarketListings)
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}

function updateLastUpdated() {
  const el = document.getElementById('last-updated');
  if (el) el.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
}

function formatTimestamp(ts) {
  if (!ts) return "Unknown";
  const d = new Date(ts);
  return d.toLocaleString();
}


function startAutoRefresh() {
  setInterval(() => loadMarketListings(), 30000);
}
