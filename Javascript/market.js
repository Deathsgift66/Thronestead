import { supabase } from '../supabaseClient.js';
import { authHeaders } from './auth.js';
import { showToast, escapeHTML } from './utils.js';
import { setupTabs } from './components/tabControl.js';

const listingsContainer = document.getElementById('market-listings');
const myListingsContainer = document.getElementById('my-listings');
const historyContainer = document.getElementById('trade-history');
const updated = document.getElementById('last-updated');
let allListings = [];

async function fetchListings() {
  try {
    const res = await fetch('/api/market/listings');
    const data = await res.json();
    allListings = data.listings || [];
    renderListings(allListings);
    updated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
  } catch {
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

function applyFilters() {
  const search = document.getElementById('market-search').value.trim().toLowerCase();
  const cat = document.getElementById('market-category').value.toLowerCase();
  let data = allListings;
  if (search) {
    data = data.filter(i => i.item.toLowerCase().includes(search));
  }
  if (cat) {
    data = data.filter(i => i.item_type.toLowerCase() === cat);
  }
  renderListings(data);
}

async function loadMyListings() {
  myListingsContainer.innerHTML = '<p>Loading...</p>';
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return (myListingsContainer.textContent = 'Not logged in.');
    const res = await fetch('/api/market/listings');
    const data = await res.json();
    const mine = (data.listings || []).filter(l => l.seller_id === user.id);
    if (!mine.length) {
      myListingsContainer.textContent = 'You have no active listings.';
      return;
    }
    myListingsContainer.innerHTML = '';
    mine.forEach(item => {
      const card = document.createElement('div');
      card.className = 'listing-card';
      card.innerHTML = `
        <div><strong>${escapeHTML(item.item)}</strong></div>
        <div>Qty: ${item.quantity}</div>
        <div>Price: ${item.price}</div>
      `;
      myListingsContainer.appendChild(card);
    });
  } catch {
    myListingsContainer.textContent = 'Failed to load listings.';
  }
}

async function loadHistory() {
  historyContainer.innerHTML = '<p>Loading...</p>';
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return (historyContainer.textContent = 'Not logged in.');
    const res = await fetch(`/api/market/history/${user.id}`);
    const data = await res.json();
    const logs = data.logs || [];
    if (!logs.length) {
      historyContainer.textContent = 'No trade history.';
      return;
    }
    historyContainer.innerHTML = '';
    logs.forEach(log => {
      const row = document.createElement('div');
      row.className = 'listing-card';
      row.innerHTML = `
        <div>${new Date(log.timestamp).toLocaleString()}</div>
        <div>${escapeHTML(log.resource)} x${log.quantity}</div>
        <div>Price: ${log.unit_price}</div>
      `;
      historyContainer.appendChild(row);
    });
  } catch {
    historyContainer.textContent = 'Failed to load history.';
  }
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
  setupTabs({ buttonSelector: '.tab', sectionSelector: '.tab-panel', onShow: id => {
    if (id === 'myListings') loadMyListings();
    if (id === 'history') loadHistory();
  }});
  document.getElementById('apply-filters')?.addEventListener('click', applyFilters);
  fetchListings();
  setInterval(fetchListings, 15000);
});
