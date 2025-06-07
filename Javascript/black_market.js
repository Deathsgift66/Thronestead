/*
Project Name: Kingmakers Rise Frontend
File Name: black_market.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Hardened Black Market system — matches current HTML

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

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

  // ✅ Initial load
  await loadBlackMarketListings();

  // ✅ Bind Place Listing form
  const listingForm = document.getElementById("listingForm");
  if (listingForm) {
    listingForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await placeNewListing();
    });
  }
});

// ✅ Load Black Market Listings
async function loadBlackMarketListings() {
  const tbody = document.getElementById("listingsTableBody");

  tbody.innerHTML = `
    <tr><td colspan="5">Loading black market listings...</td></tr>
  `;

  try {
    const res = await fetch("/api/black-market");
    const data = await res.json();

    tbody.innerHTML = "";

    if (!data.listings || data.listings.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="5">No listings available.</td></tr>
      `;
      return;
    }

    data.listings.forEach(listing => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${escapeHTML(listing.item)}</td>
        <td>${listing.price}</td>
        <td>${listing.quantity}</td>
        <td>${escapeHTML(listing.seller)}</td>
        <td>
          <button class="action-btn buy-btn" data-id="${listing.id}" data-quantity="${listing.quantity}" data-price="${listing.price}" data-item="${escapeHTML(listing.item)}">Buy</button>
        </td>
      `;

      tbody.appendChild(row);
    });

    // ✅ Bind Buy buttons
    document.querySelectorAll(".buy-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const listingId = btn.dataset.id;
        const item = btn.dataset.item;
        const price = btn.dataset.price;
        const maxQty = parseInt(btn.dataset.quantity);

        const qty = prompt(`How many '${item}' do you want to buy? (Max: ${maxQty})`);
        const qtyInt = parseInt(qty);

        if (!qtyInt || qtyInt <= 0 || qtyInt > maxQty) {
          alert("Invalid quantity.");
          return;
        }

        try {
          const res = await fetch("/api/black-market/buy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ listing_id: listingId, quantity: qtyInt })
          });
          const result = await res.json();
          alert(result.message || "Purchase completed.");
          await loadBlackMarketListings();
        } catch (err) {
          console.error("❌ Error purchasing:", err);
          alert("Purchase failed.");
        }
      });
    });

  } catch (err) {
    console.error("❌ Error loading black market:", err);
    tbody.innerHTML = `
      <tr><td colspan="5">Failed to load black market listings.</td></tr>
    `;
  }
}

// ✅ Place New Listing
async function placeNewListing() {
  const item = document.getElementById("item").value.trim();
  const price = parseFloat(document.getElementById("price").value);
  const quantity = parseInt(document.getElementById("quantity").value);

  if (!item || !price || price <= 0 || !quantity || quantity <= 0) {
    alert("Please enter valid item, price, and quantity.");
    return;
  }

  try {
    const res = await fetch("/api/black-market/place", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item, price, quantity })
    });
    const result = await res.json();
    alert(result.message || "Listing created.");
    document.getElementById("listingForm").reset();
    await loadBlackMarketListings();
  } catch (err) {
    console.error("❌ Error placing listing:", err);
    alert("Failed to place listing.");
  }
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
