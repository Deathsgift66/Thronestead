// Project Name: Kingmakers Rise©
// File Name: alliance_vault.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { RESOURCE_TYPES } from './resourceTypes.js';
import { loadCustomBoard } from './customBoard.js';
import { escapeHTML } from './utils.js';
import { setupTabs } from './components/tabControl.js';

let currentUser = null;

// ✅ Wrapper for authenticated fetch requests
function authFetch(url, options = {}) {
  options.headers = {
    ...(options.headers || {}),
    'X-User-ID': currentUser?.id || ''
  };
  return fetch(url, options);
}

// ✅ Subscribe to real-time vault updates
function subscribeToVault(allianceId) {
  supabase
    .channel(`vault_${allianceId}`)
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

// ✅ Page bootstrap
document.addEventListener("DOMContentLoaded", async () => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return (window.location.href = "login.html");
  currentUser = user;

  document.getElementById("logout-btn")?.addEventListener("click", async () => {
    await supabase.auth.signOut();
    window.location.href = "index.html";
  });

  setupTabs({ onShow: id => id === 'tab-transactions' && loadVaultHistory() });
  await Promise.all([
    loadVaultSummary(),
    loadCustomBoard({ fetchFn: authFetch }),
    loadDepositForm(),
    loadWithdrawForm(),
    loadVaultHistory()
  ]);

  const { data: allianceData } = await supabase
    .from('users')
    .select('alliance_id')
    .eq('user_id', user.id)
    .single();

  if (allianceData?.alliance_id) {
    subscribeToVault(allianceData.alliance_id);
  }

  document.getElementById('apply-trans-filter')?.addEventListener('click', loadVaultHistory);
});

// ✅ Tab control

// ✅ Vault total summary
async function loadVaultSummary() {
  const container = document.querySelector(".vault-summary");
  container.innerHTML = "<p>Loading vault totals...</p>";

  try {
    const res = await authFetch("/api/vault/resources");
    const { totals } = await res.json();

    container.innerHTML = "";
    if (!totals || Object.keys(totals).length === 0) {
      container.innerHTML = "<p>No resources in vault.</p>";
      return;
    }

    Object.entries(totals).forEach(([res, amt]) => {
      const div = document.createElement("div");
      div.classList.add("vault-resource-row");
      const pct = Math.min(100, (amt / 100000) * 100);
      div.innerHTML = `
        <strong>${escapeHTML(res)}</strong>
        <div class="vault-progress-bar">
          <div class="vault-progress-bar-fill" style="width:${pct}%"></div>
        </div>
        <span>${amt.toLocaleString()}</span>`;
      container.appendChild(div);
    });

  } catch (err) {
    console.error("❌ Vault Summary:", err);
    container.innerHTML = "<p>Failed to load vault totals.</p>";
  }
}


// ✅ Deposit interface
async function loadDepositForm() {
  const container = document.getElementById("deposit-section");
  container.innerHTML = `
    <label>Resource:</label>
    <input list="resource-options-deposit" id="deposit-resource" />
    <datalist id="resource-options-deposit">
      ${RESOURCE_TYPES.map(r => `<option value="${r}">`).join('')}
    </datalist>
    <label>Amount:</label>
    <input type="number" id="deposit-amount" min="1" />
    <button class="action-btn" id="deposit-submit">Deposit</button>
  `;

  document.getElementById("deposit-submit").addEventListener("click", async () => {
    const resource = document.getElementById("deposit-resource").value.toLowerCase().replace(/ /g, "_");
    const amount = parseInt(document.getElementById("deposit-amount").value);
    if (!resource || amount <= 0) return alert("Please enter a valid resource and amount.");

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
      console.error("❌ Deposit:", err);
      alert("Deposit failed.");
    }
  });
}

// ✅ Withdraw interface
async function loadWithdrawForm() {
  const container = document.getElementById("withdraw-section");
  container.innerHTML = `
    <label>Resource:</label>
    <input list="resource-options-withdraw" id="withdraw-resource" />
    <datalist id="resource-options-withdraw">
      ${RESOURCE_TYPES.map(r => `<option value="${r}">`).join('')}
    </datalist>
    <label>Amount:</label>
    <input type="number" id="withdraw-amount" min="1" />
    <button class="action-btn" id="withdraw-submit">Withdraw</button>
  `;

  document.getElementById("withdraw-submit").addEventListener("click", async () => {
    const resource = document.getElementById("withdraw-resource").value.toLowerCase().replace(/ /g, "_");
    const amount = parseInt(document.getElementById("withdraw-amount").value);
    if (!resource || amount <= 0) return alert("Please enter a valid resource and amount.");

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
      console.error("❌ Withdraw:", err);
      alert("Withdrawal failed.");
    }
  });
}

// ✅ Vault transaction history
async function loadVaultHistory() {
  const tbody = document.getElementById("vault-history");
  tbody.innerHTML = `<tr><td colspan="6">Loading...</td></tr>`;

  try {
    const params = new URLSearchParams();
    const action = document.getElementById('filter-action')?.value;
    const days = document.getElementById('filter-days')?.value;
    if (action) params.append('action', action);
    if (days) params.append('days', days);

    const res = await authFetch(`/api/vault/transactions?${params}`);
    const { history = [] } = await res.json();

    tbody.innerHTML = "";
    if (!history.length) {
      tbody.innerHTML = `<tr><td colspan="6">No transactions found.</td></tr>`;
      return;
    }

    history.forEach(t => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${new Date(t.created_at).toLocaleString()}</td>
        <td>${escapeHTML(t.username || t.user_id || 'System')}</td>
        <td>${escapeHTML(t.action)}</td>
        <td>${escapeHTML(t.resource_type)}</td>
        <td>${t.amount}</td>
        <td>${escapeHTML(t.notes || '')}</td>
      `;
      tbody.appendChild(row);
    });

  } catch (err) {
    console.error("❌ Vault History:", err);
    tbody.innerHTML = `<tr><td colspan="6">Failed to load history.</td></tr>`;
  }
}

