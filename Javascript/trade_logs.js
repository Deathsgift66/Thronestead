// Project Name: Thronestead©
// File Name: trade_logs.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';
import { RESOURCE_TYPES } from './resourceTypes.js';
import { setupTabs } from './components/tabControl.js';

let realtimeChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  setupTabs({ onShow: loadTradeLogs });
  initFilters();
  populateResourceOptions();
  await loadTradeLogs();
  startAutoRefresh();
  subscribeRealtime();
  applyKingdomLinks();
});

// ✅ Initialize tab switching logic

// ✅ Setup filters
function initFilters() {
  document.getElementById('applyFilters')?.addEventListener('click', loadTradeLogs);
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

    const activeTab = document.querySelector('.tab-button.active')?.dataset.target;
    const filters = {
      kingdom_id: userData.kingdom_id,
      alliance_id: userData.alliance_id,
      startDate: document.getElementById('startDate').value,
      endDate: document.getElementById('endDate').value,
      resourceType: document.getElementById('resourceType').value
    };

    const trades = await queryTrades(activeTab, filters);
    renderTradeTable(trades);
    updateSummary(trades);
    updateLastUpdated();
    applyKingdomLinks();

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
    .order('timestamp', { ascending: false })
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
    const totalPrice = t.quantity * t.unit_price;

    row.innerHTML = `
      <td>${new Date(t.timestamp).toLocaleString()}</td>
      <td>${escapeHTML(t.seller_name)}</td>
      <td>${escapeHTML(t.buyer_name)}</td>
      <td>${escapeHTML(t.resource)}</td>
      <td>${t.quantity.toLocaleString()}</td>
      <td>${totalPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
    `;

    body.appendChild(row);
  });
  applyKingdomLinks();
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
