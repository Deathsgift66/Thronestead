// Project Name: Thronestead©
// File Name: trade_logs.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';
import { RESOURCE_TYPES } from './resourceTypes.js';
import { setupTabs } from './components/tabControl.js';

let realtimeChannel = null;
let sortAsc = false;
let currentTrades = [];

document.addEventListener("DOMContentLoaded", async () => {
  setupTabs({ onShow: loadTradeLogs });
  initFilters();
  populateResourceOptions();
  await loadTradeLogs();
  startAutoRefresh();
  subscribeRealtime();
  applyKingdomLinks('#ledger-table-body td');
});

// ✅ Initialize tab switching logic

// ✅ Setup filters
function initFilters() {
  document.getElementById('applyFilters')?.addEventListener('click', loadTradeLogs);
  document.getElementById('toggleSort')?.addEventListener('click', () => {
    sortAsc = !sortAsc;
    document.getElementById('toggleSort').textContent = sortAsc ? 'Oldest \u2191' : 'Newest \u2193';
    loadTradeLogs();
  });
  document.getElementById('export-csv-btn')?.addEventListener('click', exportCSV);
}

// ✅ Populate dropdown with resource options
function populateResourceOptions() {
  const select = document.getElementById('resourceType');
  if (!select) return;

  RESOURCE_TYPES.forEach(res => {
    const opt = document.createElement('option');
    opt.value = res;
    opt.textContent = res;
    select.appendChild(opt);
  });
}

// ✅ Load Trade Log Table
async function loadTradeLogs() {
  const body = document.getElementById('ledger-table-body');
  const volumeEl = document.getElementById('total-volume');
  const countEl = document.getElementById('total-trades');
  const avgEl = document.getElementById('avg-price');

  body.innerHTML = "<tr><td colspan='6'>Loading trade logs...</td></tr>";
  volumeEl.textContent = "-";
  countEl.textContent = "-";
  avgEl.textContent = "-";

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const { data: userData } = await supabase
      .from('users')
      .select('kingdom_id, alliance_id')
      .eq('user_id', user.id)
      .single();

    const activeTab = document.querySelector('.tab-button.active')?.dataset.tab;
    const filters = {
      kingdom_id: userData.kingdom_id,
      alliance_id: userData.alliance_id,
      startDate: document.getElementById('startDate').value,
      endDate: document.getElementById('endDate').value,
      resourceType: document.getElementById('resourceType').value
    };

    const trades = await queryTrades(activeTab, filters);
    currentTrades = trades;
    renderTradeTable(trades);
    updateSummary(trades);
    updateLastUpdated();
    applyKingdomLinks('#ledger-table-body td');

  } catch (err) {
    console.error("❌ Trade Load Error:", err);
    body.innerHTML = "<tr><td colspan='6'>Failed to load trade logs.</td></tr>";
    showToast("Failed to load trade logs.");
  }
}

// ✅ Build and execute Supabase query
async function queryTrades(tab, filters) {
  let q = supabase
    .from('trade_logs')
    .select('*')
    .order('timestamp', { ascending: sortAsc })
    .limit(100);

  if (tab === 'tab-kingdom') {
    q = q.or(`buyer_id.eq.${filters.kingdom_id},seller_id.eq.${filters.kingdom_id}`);
  } else if (tab === 'tab-alliance') {
    if (!filters.alliance_id) return [];
    q = q.or(`buyer_alliance_id.eq.${filters.alliance_id},seller_alliance_id.eq.${filters.alliance_id}`);
  }

  if (filters.startDate) {
    q = q.gte('timestamp', new Date(filters.startDate).toISOString());
  }
  if (filters.endDate) {
    const end = new Date(filters.endDate);
    end.setHours(23, 59, 59, 999);
    q = q.lte('timestamp', end.toISOString());
  }
  if (filters.resourceType && filters.resourceType !== "ALL") {
    q = q.eq('resource', filters.resourceType);
  }

  const { data, error } = await q;
  if (error) throw error;
  return data;
}

// ✅ Render trade log table rows
function renderTradeTable(trades) {
  const body = document.getElementById('ledger-table-body');
  body.innerHTML = "";

  if (!trades.length) {
    body.innerHTML = "<tr><td colspan='6'>No trades found for selected filters.</td></tr>";
    return;
  }

  trades.forEach(t => {
    const row = document.createElement('tr');
    const safeQty = parseInt(t.quantity, 10) || 0;
    const safePrice = parseFloat(t.unit_price) || 0;
    const totalPrice = safeQty * safePrice;

    row.innerHTML = `
      <td>${new Date(t.timestamp).toLocaleString()}</td>
      <td class="log-entry">${escapeHTML(t.seller_name)}</td>
      <td class="log-entry">${escapeHTML(t.buyer_name)}</td>
      <td>${escapeHTML(t.resource)}</td>
      <td>${safeQty.toLocaleString()}</td>
      <td>${totalPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
    `;

    body.appendChild(row);
  });
  applyKingdomLinks('#ledger-table-body td');
}

// ✅ Update trade volume/summary
function updateSummary(trades) {
  const volumeEl = document.getElementById('total-volume');
  const countEl = document.getElementById('total-trades');
  const avgEl = document.getElementById('avg-price');

  const totalVolume = trades.reduce((sum, t) => sum + t.quantity, 0);
  const totalValue = trades.reduce((sum, t) => sum + (t.quantity * t.unit_price), 0);
  const average = totalVolume > 0 ? (totalValue / totalVolume).toFixed(2) : "-";

  volumeEl.textContent = totalVolume.toLocaleString();
  countEl.textContent = trades.length.toString();
  avgEl.textContent = average;
}

// ✅ Live update time display
function updateLastUpdated() {
  const el = document.getElementById('last-updated');
  if (el) el.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
}

function exportCSV() {
  if (!currentTrades.length) return;
  const header = 'Timestamp,Seller,Buyer,Resource,Quantity,Unit Price,Total Price\n';
  const csv = currentTrades
    .map(t => {
      const qty = parseInt(t.quantity, 10) || 0;
      const price = parseFloat(t.unit_price) || 0;
      const total = qty * price;
      return [t.timestamp, t.seller_name, t.buyer_name, t.resource, qty, price.toFixed(2), total.toFixed(2)]
        .map(v => `"${String(v).replace(/"/g, '""')}"`).join(',');
    })
    .join('\n');
  const blob = new Blob([header + csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'trade_logs.csv';
  a.click();
  URL.revokeObjectURL(url);
}

// ✅ Show alert/feedback
function showToast(msg) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast-notification';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

// ✅ Escape input to prevent XSS

// ✅ Auto Refresh every 30s
function startAutoRefresh() {
  setInterval(loadTradeLogs, 30000);
}

// ✅ Subscribe to realtime changes
function subscribeRealtime() {
  realtimeChannel = supabase
    .channel('public:trade_logs')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'trade_logs'
    }, loadTradeLogs)
    .subscribe(status => {
      const indicator = document.getElementById('realtime-indicator');
      if (indicator) {
        indicator.textContent = status === 'SUBSCRIBED' ? 'Live' : 'Offline';
        indicator.className = status === 'SUBSCRIBED' ? 'connected' : 'disconnected';
      }
    });

  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}
