/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_vault.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Full dynamic Alliance Vault page

import { supabase } from './supabaseClient.js';
import { RESOURCE_TYPES } from './resourceTypes.js';

let currentUser = null;

function authFetch(url, options = {}) {
  options.headers = {
    ...(options.headers || {}),
    'X-User-Id': currentUser?.id || ''
  };
  return fetch(url, options);
}

function subscribeToVault(allianceId) {
  supabase.channel('vault_' + allianceId)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'alliance_vault_transaction_log',
      filter: `alliance_id=eq.${allianceId}`
    }, async () => {
      await loadVaultSummary();
      await loadVaultHistory();
    })
    .subscribe();
}

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    window.location.href = "login.html";
    return;
  }
  currentUser = user;

  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  initTabs();

  // ✅ Initial load
  await loadVaultSummary();
  await loadCustomBoard();
  await loadDepositForm();
  await loadWithdrawForm();
  await loadVaultHistory();

  const { data: allianceData } = await supabase
    .from('users')
    .select('alliance_id')
    .eq('user_id', user.id)
    .single();
  if (allianceData && allianceData.alliance_id) {
    subscribeToVault(allianceData.alliance_id);
  }

  document.getElementById('apply-trans-filter').addEventListener('click', async () => {
    await loadVaultHistory();
  });
});

// ✅ Tabs
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabSections = document.querySelectorAll('.tab-section');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const target = btn.getAttribute('data-tab');

      tabButtons.forEach(b => b.classList.remove('active'));
      tabSections.forEach(section => section.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(target).classList.add('active');

      if (target === 'tab-transactions') {
        await loadVaultHistory();
      }
    });
  });
}

// ✅ Load Vault Summary
async function loadVaultSummary() {
  const container = document.querySelector(".vault-summary");
  container.innerHTML = "<p>Loading vault totals...</p>";

  try {
    const res = await authFetch("/api/vault/resources");
    const data = await res.json();

    container.innerHTML = "";
    if (!data.totals || Object.keys(data.totals).length === 0) {
      container.innerHTML = "<p>No resources in vault.</p>";
      return;
    }

    Object.entries(data.totals).forEach(([resource, amount]) => {
      const div = document.createElement("div");
      div.classList.add("vault-resource-row");
      const pct = Math.min(100, (amount / 100000) * 100);
      div.innerHTML = `
        <strong>${resource}</strong>
        <div class="vault-progress-bar">
          <div class="vault-progress-bar-fill" style="width:${pct}%"></div>
        </div>
        <span>${amount}</span>`;
      container.appendChild(div);
    });

  } catch (err) {
    console.error("❌ Error loading vault summary:", err);
    container.innerHTML = "<p>Failed to load vault totals.</p>";
  }
}

// ✅ Load Custom Board (Image + Text)
async function loadCustomBoard() {
  try {
    const res = await authFetch("/api/alliance-vault/custom-board");
    const data = await res.json();

    const imgSlot = document.getElementById("custom-image-slot");
    const textSlot = document.getElementById("custom-text-slot");

    imgSlot.innerHTML = data.image_url
      ? `<img src="${data.image_url}" alt="Vault Custom Banner" class="vault-banner-image">`
      : "<p>No custom image set.</p>";

    textSlot.innerHTML = data.custom_text
      ? `<p>${data.custom_text}</p>`
      : "<p>No custom text set.</p>";

  } catch (err) {
    console.error("❌ Error loading custom board:", err);
    document.getElementById("custom-image-slot").innerHTML = "<p>Error loading image.</p>";
    document.getElementById("custom-text-slot").innerHTML = "<p>Error loading text.</p>";
  }
}

// ✅ Load Deposit Form
async function loadDepositForm() {
  const container = document.getElementById("deposit-section");
  container.innerHTML = `
    <label for="deposit-resource">Resource:</label>
    <input list="resource-options-deposit" id="deposit-resource" />
    <datalist id="resource-options-deposit">
      ${RESOURCE_TYPES.map(r => `<option value="${r}">`).join('')}
    </datalist>
    <label for="deposit-amount">Amount:</label>
    <input type="number" id="deposit-amount" min="1" />
    <button class="action-btn" id="deposit-submit">Deposit</button>
  `;

  document.getElementById("deposit-submit").addEventListener("click", async () => {
    const raw = document.getElementById("deposit-resource").value.trim();
    const resource = raw.toLowerCase().replace(/ /g, "_");
    const amount = parseInt(document.getElementById("deposit-amount").value);

    if (!resource || !amount || amount <= 0) {
      alert("Please enter a valid resource and amount.");
      return;
    }

    try {
      const res = await authFetch("/api/vault/deposit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resource, amount })
      });
      const result = await res.json();
      alert(result.message || "Deposit successful.");
      await loadVaultSummary();
      await loadVaultHistory();
    } catch (err) {
      console.error("❌ Error during deposit:", err);
      alert("Deposit failed.");
    }
  });
}

// ✅ Load Withdraw Form
async function loadWithdrawForm() {
  const container = document.getElementById("withdraw-section");
  container.innerHTML = `
    <label for="withdraw-resource">Resource:</label>
    <input list="resource-options-withdraw" id="withdraw-resource" />
    <datalist id="resource-options-withdraw">
      ${RESOURCE_TYPES.map(r => `<option value="${r}">`).join('')}
    </datalist>
    <label for="withdraw-amount">Amount:</label>
    <input type="number" id="withdraw-amount" min="1" />
    <button class="action-btn" id="withdraw-submit">Withdraw</button>
  `;

  document.getElementById("withdraw-submit").addEventListener("click", async () => {
    const raw = document.getElementById("withdraw-resource").value.trim();
    const resource = raw.toLowerCase().replace(/ /g, "_");
    const amount = parseInt(document.getElementById("withdraw-amount").value);

    if (!resource || !amount || amount <= 0) {
      alert("Please enter a valid resource and amount.");
      return;
    }

    try {
      const res = await authFetch("/api/vault/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resource, amount })
      });
      const result = await res.json();
      alert(result.message || "Withdrawal successful.");
      await loadVaultSummary();
      await loadVaultHistory();
    } catch (err) {
      console.error("❌ Error during withdrawal:", err);
      alert("Withdrawal failed.");
    }
  });
}

// ✅ Load Vault History
async function loadVaultHistory() {
  const tbody = document.getElementById("vault-history");
  tbody.innerHTML = `<tr><td colspan="6">Loading...</td></tr>`;

  try {
    const actionFilter = document.getElementById('filter-action').value;
    const params = new URLSearchParams();
    if (actionFilter) params.append('action', actionFilter);
    const res = await authFetch(`/api/vault/transactions?${params.toString()}`);
    const data = await res.json();

    tbody.innerHTML = "";
    if (!data.history || data.history.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6">No transactions found.</td></tr>`;
      return;
    }

    data.history.forEach(t => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${new Date(t.created_at).toLocaleString()}</td>
        <td>${t.username || t.user_id || 'System'}</td>
        <td>${t.action}</td>
        <td>${t.resource_type}</td>
        <td>${t.amount}</td>
        <td>${t.notes || ''}</td>
      `;
      tbody.appendChild(row);
    });

  } catch (err) {
    console.error("❌ Error loading vault history:", err);
    tbody.innerHTML = `<tr><td colspan="6">Failed to load history.</td></tr>`;
  }
}
