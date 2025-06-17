// Project Name: Thronestead©
// File Name: market.js
// Updated JS module using Supabase queries and realtime
import { supabase } from './supabaseClient.js';

const indicator = document.getElementById('realtime-indicator');
const updated = document.getElementById('last-updated');
const listingsContainer = document.getElementById('market-listings');
const myListingsContainer = document.getElementById('my-listings');
const historyContainer = document.getElementById('trade-history');
const searchInput = document.getElementById('market-search');
const categorySelect = document.getElementById('market-category');

let allListings = [];

// Format Timestamp
const formatTime = (isoStr) => new Date(isoStr).toLocaleString();

// Load Listings
async function fetchMarketListings() {
  const { data, error } = await supabase
    .from('market_listings')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(50);

  if (error) {
    listingsContainer.innerHTML = '<p>❌ Failed to load listings.</p>';
    indicator.textContent = 'Offline';
    indicator.classList.add('disconnected');
    return;
  }

  allListings = data;
  renderListings(data);
  updated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
  indicator.textContent = 'Online';
  indicator.classList.remove('disconnected');
}

// Render Listings
function renderListings(data) {
  listingsContainer.innerHTML = '';
  if (!data.length) {
    listingsContainer.innerHTML = '<p>No items listed.</p>';
    return;
  }

  data.forEach((item) => {
    const card = document.createElement('div');
    card.className = 'listing-card';
    card.innerHTML = `
      <div><strong>${item.item_name}</strong></div>
      <div>Qty: ${item.quantity}</div>
      <div>Price: ${item.price_per_unit}g</div>
      <div>Seller: ${item.seller_name}</div>
      <div class="listing-time">${formatTime(item.created_at)}</div>
    `;
    listingsContainer.appendChild(card);
  });
}

// Filter Logic
const applyBtn = document.getElementById('apply-filters');
if (applyBtn) {
  applyBtn.addEventListener('click', () => {
    const term = searchInput.value.toLowerCase();
    const category = categorySelect.value;
    const filtered = allListings.filter(
      (i) =>
        (!term || i.item_name.toLowerCase().includes(term)) &&
        (!category || i.category === category)
    );
    renderListings(filtered);
  });
}

// My Listings
async function loadUserListings() {
  const user = await supabase.auth.getUser();
  const userId = user?.data?.user?.id;
  if (!userId) return;

  const { data, error } = await supabase
    .from('market_listings')
    .select('*')
    .eq('seller_id', userId);

  myListingsContainer.innerHTML = '';
  if (error || !data.length) {
    myListingsContainer.innerHTML = '<p>No active listings.</p>';
    return;
  }

  data.forEach((item) => {
    const div = document.createElement('div');
    div.className = 'listing-card';
    div.innerHTML = `
      <strong>${item.item_name}</strong> — ${item.quantity} @ ${item.price_per_unit}g
      <div>Posted: ${formatTime(item.created_at)}</div>
      <button onclick="cancelListing(${item.id})">Cancel</button>
    `;
    myListingsContainer.appendChild(div);
  });
}

// Cancel Listing
window.cancelListing = async (listingId) => {
  const { error } = await supabase
    .from('market_listings')
    .delete()
    .eq('id', listingId);

  if (error) {
    alert('❌ Failed to cancel.');
    return;
  }
  loadUserListings();
  fetchMarketListings();
};

// Trade History
async function loadTradeHistory() {
  const user = await supabase.auth.getUser();
  const userId = user?.data?.user?.id;
  if (!userId) return;

  const { data, error } = await supabase
    .from('market_history')
    .select('*')
    .or(`buyer_id.eq.${userId},seller_id.eq.${userId}`)
    .order('created_at', { ascending: false })
    .limit(20);

  historyContainer.innerHTML = '';
  if (error || !data.length) {
    historyContainer.innerHTML = '<p>No recent trades.</p>';
    return;
  }

  data.forEach((t) => {
    const row = document.createElement('div');
    row.className = 'listing-card';
    row.innerHTML = `
      <strong>${t.item_name}</strong><br />
      ${t.quantity} units @ ${t.price_per_unit}g<br />
      Seller: ${t.seller_name} | Buyer: ${t.buyer_name}<br />
      <span class="listing-time">${formatTime(t.created_at)}</span>
    `;
    historyContainer.appendChild(row);
  });
}

// Realtime listener
supabase
  .channel('market_updates')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'market_listings' }, fetchMarketListings)
  .subscribe();

// Initialize
fetchMarketListings();
loadUserListings();
loadTradeHistory();
