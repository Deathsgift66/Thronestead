import { supabase } from './supabaseClient.js';

let listings = [];
let currentListing = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  document.getElementById('searchInput').addEventListener('input', renderListings);
  document.getElementById('sortSelect').addEventListener('change', renderListings);
  document.getElementById('closeModal').addEventListener('click', closeModal);
  document.getElementById('confirmPurchase').addEventListener('click', confirmPurchase);

  await loadListings();
  await loadHistory();
});

async function loadListings() {
  const res = await fetch('/api/black-market/listings');
  const data = await res.json();
  listings = data.listings || [];
  renderListings();
}

function renderListings() {
  const search = document.getElementById('searchInput').value.toLowerCase();
  const sort = document.getElementById('sortSelect').value;
  let filtered = listings.filter(l => l.item_name.toLowerCase().includes(search));
  if (sort === 'price') filtered.sort((a,b)=>a.price_per_unit-b.price_per_unit);
  if (sort === 'quantity') filtered.sort((a,b)=>b.stock_remaining-a.stock_remaining);
  if (sort === 'expiry') filtered.sort((a,b)=>new Date(a.expires_at)-new Date(b.expires_at));

  const grid = document.getElementById('listingsGrid');
  grid.innerHTML = '';
  filtered.forEach(l => {
    const card = document.createElement('div');
    card.className = 'listing-card';
    card.innerHTML = `
      <img src="Assets/1.png" alt="${l.item_name}">
      <strong>${escapeHTML(l.item_name)}</strong><br>
      ${l.stock_remaining} available<br>
      ${l.price_per_unit} ${l.currency_type}
    `;
    card.addEventListener('click', () => openModal(l));
    grid.appendChild(card);
  });
}

function openModal(listing) {
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
  const qty = parseInt(document.getElementById('purchaseQty').value);
  if (!currentListing || !qty || qty < 1 || qty > currentListing.stock_remaining) return;

  await fetch('/api/black-market/purchase', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ listing_id: currentListing.id, quantity: qty, kingdom_id: 'demo-kingdom' })
  });

  closeModal();
  await loadListings();
  await loadHistory();
}

async function loadHistory() {
  const res = await fetch('/api/black-market/history?kingdom_id=demo-kingdom');
  const data = await res.json();
  const container = document.getElementById('purchaseHistory');
  container.innerHTML = '';
  (data.trades || []).forEach(t => {
    const div = document.createElement('div');
    div.className = 'history-item';
    div.textContent = `${t.item_name} x${t.quantity} at ${t.price_per_unit} ${t.currency_type}`;
    container.appendChild(div);
  });
}

function escapeHTML(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
