/*
Project Name: Kingmakers Rise Frontend
File Name: resources.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';
import { fetchJson } from './fetchJson.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  // ✅ Initial load
  await loadResourcesNexus();
});

// ✅ Load Resources Nexus
async function loadResourcesNexus() {
  const summaryEl = document.getElementById('resource-summary');
  const resourceTableEl = document.getElementById('resource-table');
  const vaultTableEl = document.getElementById('vault-table');
  const simulatorsEl = document.getElementById('simulators');

  // Placeholders
  summaryEl.innerHTML = "<p>Loading resource summary...</p>";
  resourceTableEl.innerHTML = "<p>Loading resources...</p>";
  vaultTableEl.innerHTML = "<p>Loading vault...</p>";
  simulatorsEl.innerHTML = "<p>Loading simulators...</p>";

  try {
    const { data: { session } } = await supabase.auth.getSession();
    const uid = session?.user?.id;
    if (!uid) throw new Error('No user');
    const token = session.access_token;

    const headers = { Authorization: `Bearer ${token}`, 'X-User-ID': uid };

    const { resources: resourcesData } = await fetchJson('/api/resources', { headers });

    let vaultData = null;
    try {
      const { totals } = await fetchJson('/api/vault/resources', { headers });
      vaultData = totals;
    } catch {
      vaultData = null;
    }

    // ✅ Render resource summary
    renderResourceSummary(resourcesData);

    // ✅ Render resource table
    renderResourceTable(resourcesData);

    // ✅ Render vault table
    renderVaultTable(vaultData);

    // ✅ Render simulators panel
    renderSimulators();

    // ✅ Subscribe to realtime updates
    subscribeToResourceUpdates();

  } catch (err) {
    console.error("❌ Error loading Resources Nexus:", err);
    showToast("Failed to load Resources Nexus.");
  }
}

// ✅ Render Resource Summary
function renderResourceSummary(resources) {
  const summaryEl = document.getElementById('resource-summary');
  summaryEl.innerHTML = "";

  const totalResources = Object.entries(resources)
    .filter(([key]) => key !== "kingdom_id")
    .reduce((sum, [key, value]) => sum + value, 0);

  summaryEl.innerHTML = `
    <h3>Total Resources</h3>
    <p>${formatNumber(totalResources)} units across all categories.</p>
  `;
}

// ✅ Render Resource Table
function renderResourceTable(resources) {
  const tableEl = document.getElementById('resource-table');
  tableEl.innerHTML = "";

  const resourceEntries = Object.entries(resources)
    .filter(([key]) => key !== "kingdom_id")
    .sort(([aKey], [bKey]) => aKey.localeCompare(bKey));

  resourceEntries.forEach(([resource, amount]) => {
    const card = document.createElement("div");
    card.classList.add("resource-card");

    card.innerHTML = `
      <h4>${formatResourceName(resource)}</h4>
      <p>Amount: ${formatNumber(amount)}</p>
    `;

    tableEl.appendChild(card);
  });
}

// ✅ Render Vault Table
function renderVaultTable(vaultData) {
  const vaultEl = document.getElementById('vault-table');
  vaultEl.innerHTML = "";

  if (!vaultData) {
    vaultEl.innerHTML = "<p>You are not in an alliance, or no vault data found.</p>";
    return;
  }

  const vaultEntries = Object.entries(vaultData)
    .filter(([key]) => key !== "alliance_id")
    .sort(([aKey], [bKey]) => aKey.localeCompare(bKey));

  vaultEntries.forEach(([resource, amount]) => {
    const card = document.createElement("div");
    card.classList.add("vault-card");

    card.innerHTML = `
      <h4>${formatResourceName(resource)}</h4>
      <p>Amount: ${formatNumber(amount)}</p>
    `;

    vaultEl.appendChild(card);
  });
}

// ✅ Render Simulators
function renderSimulators() {
  const simulatorsEl = document.getElementById('simulators');
  simulatorsEl.innerHTML = "";

  const simulatorPanel = document.createElement("div");
  simulatorPanel.classList.add("simulator-panel");

  simulatorPanel.innerHTML = `
    <h3>Resource Simulators</h3>
    <p>Production estimators, trade calculators and efficiency tools.</p>
  `;

  simulatorsEl.appendChild(simulatorPanel);
}

// ✅ Helper: Format Resource Name
function formatResourceName(resourceKey) {
  return resourceKey
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());
}

// ✅ Helper: Format Number
function formatNumber(num) {
  return num.toLocaleString();
}

// ✅ Helper: Toast
function showToast(msg) {
  const toastEl = document.getElementById('toast');
  toastEl.textContent = msg;
  toastEl.classList.add("show");

  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
}

// ✅ Realtime subscriptions
function subscribeToResourceUpdates() {
  supabase.auth.getUser().then(({ data }) => {
    const uid = data?.user?.id;
    if (!uid) return;
    supabase
      .from('users')
      .select('kingdom_id, alliance_id')
      .eq('user_id', uid)
      .single()
      .then(({ data }) => {
        const kid = data?.kingdom_id;
        const aid = data?.alliance_id;
        if (kid) {
          supabase
            .channel('kr-resources-' + kid)
            .on('postgres_changes', { event: '*', schema: 'public', table: 'kingdom_resources', filter: `kingdom_id=eq.${kid}` }, (payload) => {
              if (payload.new) {
                renderResourceSummary(payload.new);
                renderResourceTable(payload.new);
              }
            })
            .subscribe();
        }
        if (aid) {
          supabase
            .channel('kr-vault-' + aid)
            .on('postgres_changes', { event: '*', schema: 'public', table: 'alliance_vault', filter: `alliance_id=eq.${aid}` }, (payload) => {
              if (payload.new) {
                renderVaultTable(payload.new);
              }
            })
            .subscribe();
        }
      });
  });
}
