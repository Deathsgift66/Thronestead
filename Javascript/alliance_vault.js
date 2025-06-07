/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_vault.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Full dynamic Alliance Vault page

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
import { RESOURCE_TYPES } from './resourceTypes.js';
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

  // ✅ Initial load
  await loadVaultSummary();
  await loadCustomBoard();
  await loadDepositForm();
  await loadWithdrawForm();
  await loadVaultHistory();
});

// ✅ Load Vault Summary
async function loadVaultSummary() {
  const container = document.querySelector(".vault-summary");
  container.innerHTML = "<p>Loading vault totals...</p>";

  try {
    const res = await fetch("/api/alliance-vault/summary");
    const data = await res.json();

    container.innerHTML = "";
    if (!data.totals || Object.keys(data.totals).length === 0) {
      container.innerHTML = "<p>No resources in vault.</p>";
      return;
    }

    Object.entries(data.totals).forEach(([resource, amount]) => {
      const div = document.createElement("div");
      div.classList.add("vault-resource-row");
      div.innerHTML = `<strong>${resource}</strong>: ${amount}`;
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
    const res = await fetch("/api/alliance-vault/custom-board");
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
    const resource = document.getElementById("deposit-resource").value.trim();
    const amount = parseInt(document.getElementById("deposit-amount").value);

    if (!resource || !amount || amount <= 0) {
      alert("Please enter a valid resource and amount.");
      return;
    }

    try {
      const res = await fetch("/api/alliance-vault/deposit", {
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
    const resource = document.getElementById("withdraw-resource").value.trim();
    const amount = parseInt(document.getElementById("withdraw-amount").value);

    if (!resource || !amount || amount <= 0) {
      alert("Please enter a valid resource and amount.");
      return;
    }

    try {
      const res = await fetch("/api/alliance-vault/withdraw", {
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
  const container = document.getElementById("vault-history");
  container.innerHTML = "<p>Loading vault history...</p>";

  try {
    const res = await fetch("/api/alliance-vault/history");
    const data = await res.json();

    container.innerHTML = "";
    if (!data.history || data.history.length === 0) {
      container.innerHTML = "<p>No transaction history available.</p>";
      return;
    }

    const list = document.createElement("ul");
    data.history.forEach(entry => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${entry.timestamp}</strong> — ${entry.user} ${entry.action} ${entry.amount} ${entry.resource}
      `;
      list.appendChild(li);
    });

    container.appendChild(list);

  } catch (err) {
    console.error("❌ Error loading vault history:", err);
    container.innerHTML = "<p>Failed to load vault history.</p>";
  }
}
