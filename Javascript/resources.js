// resources.js — FINAL AAA/SSS VERSION — 6.2.25
// Resources Nexus Page Controller — FINAL architecture

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

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
    // ✅ Load user
    const { data: { user } } = await supabase.auth.getUser();

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('kingdom_id, alliance_id')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const kingdomId = userData.kingdom_id;
    const allianceId = userData.alliance_id;

    // ✅ Load kingdom resources
    const { data: resourcesData, error: resourcesError } = await supabase
      .from('kingdom_resources')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .single();

    if (resourcesError) throw resourcesError;

    // ✅ Load alliance vault (if in alliance)
    let vaultData = null;
    if (allianceId) {
      const { data, error } = await supabase
        .from('alliance_vault')
        .select('*')
        .eq('alliance_id', allianceId)
        .single();

      if (error) {
        console.warn("No vault data found.");
      } else {
        vaultData = data;
      }
    }

    // ✅ Render resource summary
    renderResourceSummary(resourcesData);

    // ✅ Render resource table
    renderResourceTable(resourcesData);

    // ✅ Render vault table
    renderVaultTable(vaultData);

    // ✅ Render simulators panel (placeholder for now)
    renderSimulators();

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

// ✅ Render Simulators (placeholder)
function renderSimulators() {
  const simulatorsEl = document.getElementById('simulators');
  simulatorsEl.innerHTML = "";

  const placeholder = document.createElement("div");
  placeholder.classList.add("simulator-placeholder");

  placeholder.innerHTML = `
    <h3>Resource Simulators</h3>
    <p>Coming soon: production estimators, trade calculators, efficiency tools...</p>
  `;

  simulatorsEl.appendChild(placeholder);
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
