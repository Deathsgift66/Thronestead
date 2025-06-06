/*
Project Name: Kingmakers Rise Frontend
File Name: trade_logs.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
import { RESOURCE_TYPES } from './resourceTypes.js';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  initTabs();
  initFilters();
  populateResourceOptions();
  await loadTradeLogs();
});

// ✅ Tabs
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabSections = document.querySelectorAll('.tab-section');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const target = btn.getAttribute('data-target');

      tabButtons.forEach(b => b.classList.remove('active'));
      tabSections.forEach(section => section.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(target).classList.add('active');

      // ✅ Reload trades when switching tabs
      await loadTradeLogs();
    });
  });
}

// ✅ Filters
function initFilters() {
  const applyFiltersBtn = document.getElementById('applyFilters');
  applyFiltersBtn.addEventListener('click', async () => {
    await loadTradeLogs();
  });
}

// ✅ Populate Resource Options
function populateResourceOptions() {
  const selectEl = document.getElementById('resourceType');
  if (!selectEl) return;
  RESOURCE_TYPES.forEach(res => {
    const opt = document.createElement('option');
    opt.value = res;
    opt.textContent = res;
    selectEl.appendChild(opt);
  });
}

// ✅ Load Trade Logs
async function loadTradeLogs() {
  const ledgerBodyEl = document.getElementById('ledger-table-body');
  const totalVolumeEl = document.getElementById('total-volume');
  const totalTradesEl = document.getElementById('total-trades');
  const avgPriceEl = document.getElementById('avg-price');

  // ✅ Clear table and summary
  ledgerBodyEl.innerHTML = "<tr><td colspan='6'>Loading trade logs...</td></tr>";
  totalVolumeEl.textContent = "-";
  totalTradesEl.textContent = "-";
  avgPriceEl.textContent = "-";

  try {
    // ✅ Determine active tab
    const activeTab = document.querySelector('.tab-button.active')?.getAttribute('data-target');

    const { data: { user } } = await supabase.auth.getUser();

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('kingdom_id, alliance_id')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const kingdomId = userData.kingdom_id;
    const allianceId = userData.alliance_id;

    // ✅ Build query
    let query = supabase
      .from('trade_logs')
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(100);

    // ✅ Apply tab filter
    if (activeTab === 'tab-kingdom') {
      query = query.or(`buyer_id.eq.${kingdomId},seller_id.eq.${kingdomId}`);
    } else if (activeTab === 'tab-alliance') {
      if (allianceId) {
        query = query.or(`buyer_alliance_id.eq.${allianceId},seller_alliance_id.eq.${allianceId}`);
      } else {
        ledgerBodyEl.innerHTML = "<tr><td colspan='6'>You are not in an alliance.</td></tr>";
        return;
      }
    }
    // Else "tab-global" → no extra filter

    // ✅ Apply date filters
    const startDateVal = document.getElementById('startDate').value;
    const endDateVal = document.getElementById('endDate').value;

    if (startDateVal) {
      const startDate = new Date(startDateVal).toISOString();
      query = query.gte('timestamp', startDate);
    }

    if (endDateVal) {
      // Set to end of day
      const endDate = new Date(endDateVal);
      endDate.setHours(23, 59, 59, 999);
      const endDateISO = endDate.toISOString();
      query = query.lte('timestamp', endDateISO);
    }

    // ✅ Apply resource filter
    const resourceType = document.getElementById('resourceType').value;
    if (resourceType && resourceType !== "ALL") {
      query = query.eq('resource', resourceType);
    }

    // ✅ Execute query
    const { data: trades, error: tradesError } = await query;

    if (tradesError) throw tradesError;

    // ✅ Render table
    ledgerBodyEl.innerHTML = "";

    if (trades.length === 0) {
      ledgerBodyEl.innerHTML = "<tr><td colspan='6'>No trades found for selected filters.</td></tr>";
      return;
    }

    let totalVolume = 0;
    let totalTrades = trades.length;
    let totalValue = 0;

    trades.forEach(trade => {
      const row = document.createElement("tr");

      const volume = trade.quantity;
      const price = trade.unit_price;
      const value = volume * price;

      totalVolume += volume;
      totalValue += value;

      row.innerHTML = `
        <td>${new Date(trade.timestamp).toLocaleString()}</td>
        <td>${escapeHTML(trade.resource)}</td>
        <td>${volume.toLocaleString()}</td>
        <td>${price.toFixed(2)}</td>
        <td>${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
        <td>${escapeHTML(trade.buyer_name)} ⇄ ${escapeHTML(trade.seller_name)}</td>
      `;

      ledgerBodyEl.appendChild(row);
    });

    // ✅ Update summary
    totalVolumeEl.textContent = totalVolume.toLocaleString();
    totalTradesEl.textContent = totalTrades.toString();
    avgPriceEl.textContent = totalTrades > 0 ? (totalValue / totalVolume).toFixed(2) : "-";

  } catch (err) {
    console.error("❌ Error loading trade logs:", err);
    ledgerBodyEl.innerHTML = "<tr><td colspan='6'>Failed to load trade logs.</td></tr>";
    showToast("Failed to load trade logs.");
  }
}

// ✅ Helper: Toast
function showToast(msg) {
  let toastEl = document.getElementById('toast');

  // Inject toast if not present
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.id = "toast";
    toastEl.className = "toast-notification";
    document.body.appendChild(toastEl);
  }

  toastEl.textContent = msg;
  toastEl.classList.add("show");

  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
}

// ✅ Helper: Escape HTML
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
