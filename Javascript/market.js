/*
Project Name: Kingmakers Rise Frontend
File Name: market.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let currentUserId = null;
let realtimeChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }
  currentUserId = session.user.id;

  // ✅ Setup tabs
  setupTabs();

  subscribeRealtime();
  startAutoRefresh();

  // ✅ Load default tab → Browse Listings
  await loadMarketListings();
});

// ✅ Setup Tabs
function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const targetId = btn.getAttribute("data-tab");

      // Toggle active state
      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanels.forEach(panel => panel.classList.add("hidden"));

      btn.classList.add("active");
      document.getElementById(targetId).classList.remove("hidden");

      // Load corresponding data
      if (targetId === "market-listings") {
        await loadMarketListings();
      } else if (targetId === "my-listings") {
        await loadMyListings();
      } else if (targetId === "trade-history") {
        await loadTradeHistory();
      }
    });
  });
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

    if (!data.listings || data.listings.length === 0) {
      container.innerHTML = "<p>No active listings found.</p>";
      return;
    }

    const list = document.createElement("ul");

    data.listings.forEach(listing => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${escapeHTML(listing.item_name)}</strong> — ${listing.quantity} units @ ${listing.price} gold/unit 
        <br> Seller: ${escapeHTML(listing.seller_name)}
      `;
      list.appendChild(li);
    });

    container.appendChild(list);
    updateLastUpdated();
  } catch (err) {
    console.error("❌ Error loading market listings:", err);
    container.innerHTML = "<p>Failed to load market listings.</p>";
  }
}

// ✅ Load My Listings
async function loadMyListings() {
  const container = document.getElementById("my-listings");
  container.innerHTML = "<p>Loading your listings...</p>";

  try {
    const res = await fetch("/api/market/my_listings", {
      headers: { 'X-User-ID': currentUserId }
    });
    const data = await res.json();

    container.innerHTML = "";

    if (!data.listings || data.listings.length === 0) {
      container.innerHTML = "<p>You have no active listings.</p>";
      return;
    }

    const list = document.createElement("ul");

    data.listings.forEach(listing => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${escapeHTML(listing.item_name)}</strong> — ${listing.quantity} units @ ${listing.price} gold/unit 
        <br> <button class="action-btn cancel-btn" data-listing-id="${listing.listing_id}">Cancel</button>
      `;
      list.appendChild(li);
    });

    container.appendChild(list);

    // ✅ Bind Cancel buttons
    document.querySelectorAll(".cancel-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const listingId = btn.dataset.listingId;

        if (!confirm("Are you sure you want to cancel this listing?")) {
          return;
        }

        try {
          const res = await fetch("/api/market/cancel_listing", {
            method: "POST",
            headers: { "Content-Type": "application/json", 'X-User-ID': currentUserId },
            body: JSON.stringify({ listing_id: listingId })
          });

          const result = await res.json();

          if (!res.ok) {
            throw new Error(result.error || "Failed to cancel listing.");
          }

          alert(result.message || "Listing canceled.");
          await loadMyListings();

        } catch (err) {
          console.error("❌ Error cancelling listing:", err);
          alert("Failed to cancel listing.");
        }
      });
    });

  } catch (err) {
    console.error("❌ Error loading my listings:", err);
    container.innerHTML = "<p>Failed to load your listings.</p>";
  }
  updateLastUpdated();
}

// ✅ Load Trade History
async function loadTradeHistory() {
  const container = document.getElementById("trade-history");
  container.innerHTML = "<p>Loading trade history...</p>";

  try {
    const res = await fetch("/api/market/history", {
      headers: { 'X-User-ID': currentUserId }
    });
    const data = await res.json();

    container.innerHTML = "";

    if (!data.trades || data.trades.length === 0) {
      container.innerHTML = "<p>No trade history found.</p>";
      return;
    }

    const list = document.createElement("ul");

    data.trades.forEach(trade => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${escapeHTML(trade.item_name)}</strong> — ${trade.quantity} units @ ${trade.price} gold/unit 
        <br> Buyer: ${escapeHTML(trade.buyer_name)} — Seller: ${escapeHTML(trade.seller_name)} 
        <br> Completed: ${formatTimestamp(trade.completed_at)}
      `;
      list.appendChild(li);
    });

    container.appendChild(list);
    updateLastUpdated();
  } catch (err) {
    console.error("❌ Error loading trade history:", err);
    container.innerHTML = "<p>Failed to load trade history.</p>";
  }
}

// ✅ Format Timestamp
function formatTimestamp(ts) {
  if (!ts) return "Unknown";
  const date = new Date(ts);
  return date.toLocaleString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit"
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

function updateLastUpdated() {
  const el = document.getElementById('last-updated');
  if (el) el.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
}

function startAutoRefresh() {
  setInterval(() => {
    loadMarketListings();
  }, 30000);
}

function subscribeRealtime() {
  realtimeChannel = supabase
    .channel('public:market_listings')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'market_listings' }, () => {
      loadMarketListings();
    })
    .subscribe(status => {
      const indicator = document.getElementById('realtime-indicator');
      if (indicator) {
        if (status === 'SUBSCRIBED') {
          indicator.textContent = 'Live';
          indicator.className = 'connected';
        } else {
          indicator.textContent = 'Offline';
          indicator.className = 'disconnected';
        }
      }
    });

  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}
