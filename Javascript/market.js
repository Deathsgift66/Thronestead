import { authHeaders } from './auth.js';
import { showToast, escapeHTML } from './utils.js';

const listingsContainer = document.getElementById('market-listings');
const updated = document.getElementById('last-updated');
let allListings = [];

async function fetchListings() {
  try {
    const res = await fetch('/api/market/listings');
    const data = await res.json();
    allListings = data.listings || [];
    renderListings(allListings);
    updated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
  } catch (e) {
    listingsContainer.textContent = 'Failed to load listings.';
  }
}

function renderListings(data) {
  listingsContainer.innerHTML = '';
  if (!data.length) {
    listingsContainer.textContent = 'No items listed.';
    return;
  }

  data.forEach((item) => {
    const card = document.createElement('div');
    card.className = 'listing-card';
    card.innerHTML = `
      <div><strong>${escapeHTML(item.item)}</strong></div>
      <div>Type: ${item.item_type}</div>
      <div>Qty: ${item.quantity}</div>
      <div>Price: ${item.price}</div>
      <button class="buy-btn">Buy</button>
    `;
    card.querySelector('.buy-btn').addEventListener('click', () => openPurchase(item));
    listingsContainer.appendChild(card);
  });
}

async function openPurchase(item) {
  const qty = 1;
  const headers = await authHeaders();
  await fetch('/api/market/buy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify({ listing_id: item.listing_id, quantity: qty }),
  }).then(() => {
    showToast(`Purchased ${item.item}`);
    fetchListings();
  }).catch(() => showToast('Purchase failed'));
}

document.addEventListener('DOMContentLoaded', () => {
  fetchListings();
  setInterval(fetchListings, 15000);
});
