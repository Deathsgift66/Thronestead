// Project Name: Thronestead©
// File Name: resources.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { fetchJson } from './fetchJson.js';

document.addEventListener("DOMContentLoaded", async () => {
  await loadResourcesNexus();
});

// ✅ Load the full Resources Nexus page content
async function loadResourcesNexus() {
  const summaryEl = document.getElementById('resource-summary');
  const resourceTableEl = document.getElementById('resource-table');
  const vaultTableEl = document.getElementById('vault-table');
  const simulatorsEl = document.getElementById('simulators');

  // Initial placeholders
  summaryEl.innerHTML = "<p>Loading resource summary...</p>";
  resourceTableEl.innerHTML = "<p>Loading resources...</p>";
  vaultTableEl.innerHTML = "<p>Loading vault...</p>";
  simulatorsEl.innerHTML = "<p>Loading simulators...</p>";

  try {
    const { data: { session } } = await supabase.auth.getSession();
    const uid = session?.user?.id;
    if (!uid) throw new Error('User not authenticated');

    const token = session.access_token;
    const headers = { Authorization: `Bearer ${token}`, 'X-User-ID': uid };

    // ✅ Load kingdom resources
    const { resources: resourcesData } = await fetchJson('/api/resources', { headers });

    // ✅ Attempt alliance vault fetch
    let vaultData = null;
    try {
      const { totals } = await fetchJson('/api/vault/resources', { headers });
      vaultData = totals;
    } catch {
      vaultData = null;
    }

    renderResourceSummary(resourcesData);
    renderResourceTable(resourcesData);
    renderVaultTable(vaultData);
    renderSimulators();
    subscribeToResourceUpdates();

  } catch (err) {
    console.error("❌ Error loading Resources Nexus:", err);
    showToast("Failed to load Resources Nexus.");
  }
}

// ✅ Display a total resource summary
function renderResourceSummary(resources) {
  const summaryEl = document.getElementById('resource-summary');
  summaryEl.innerHTML = "";

  const totalResources = Object.entries(resources)
    .filter(([key]) => key !== "kingdom_id")
    .reduce((sum, [, val]) => sum + (val || 0), 0);

  summaryEl.innerHTML = `
    <h3>Total Resources</h3>
    <p>${formatNumber(totalResources)} units across all categories.</p>
  `;
}

// ✅ Show per-resource stats
function renderResourceTable(resources) {
  const tableEl = document.getElementById('resource-table');
  tableEl.innerHTML = "";

  const resourceEntries = Object.entries(resources)
    .filter(([k]) => k !== "kingdom_id")
    .sort(([a], [b]) => a.localeCompare(b));

  resourceEntries.forEach(([key, value]) => {
    const card = document.createElement("div");
    card.className = "resource-card";
    card.innerHTML = `
      <h4>${formatResourceName(key)}</h4>
      <p>Amount: ${formatNumber(value)}</p>
    `;
    tableEl.appendChild(card);
  });
}

// ✅ Show alliance vault holdings
function renderVaultTable(vault) {
  const vaultEl = document.getElementById('vault-table');
  vaultEl.innerHTML = "";

  if (!vault) {
    vaultEl.innerHTML = "<p>You are not in an alliance, or no vault data found.</p>";
    return;
  }

  const entries = Object.entries(vault)
    .filter(([k]) => k !== "alliance_id")
    .sort(([a], [b]) => a.localeCompare(b));

  entries.forEach(([key, value]) => {
    const card = document.createElement("div");
    card.className = "vault-card";
    card.innerHTML = `
      <h4>${formatResourceName(key)}</h4>
      <p>Amount: ${formatNumber(value)}</p>
    `;
    vaultEl.appendChild(card);
  });
}

// ✅ Provide simulator section (stub)
function renderSimulators() {
  const el = document.getElementById('simulators');
  el.innerHTML = "";

  const panel = document.createElement("div");
  panel.className = "simulator-panel";

  panel.innerHTML = `
    <h3>Resource Simulators</h3>
    <p class="text-muted">Estimate production rates, trade values, and net efficiency.</p>
    <ul>
      <li><a href="#" class="sim-link">🔧 Production Efficiency Simulator</a></li>
      <li><a href="#" class="sim-link">📈 Market Value Calculator</a></li>
      <li><a href="#" class="sim-link">⚖️ Trade Ratio Evaluator</a></li>
    </ul>
  `;

  el.appendChild(panel);

  panel.querySelectorAll('.sim-link').forEach(a =>
    a.addEventListener('click', e => {
      e.preventDefault();
      alert('🛠️ Simulator tools are coming soon.');
    })
  );
}

// ✅ Format resource keys to display-friendly names
function formatResourceName(key) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, char => char.toUpperCase());
}

// ✅ Thousands separator
function formatNumber(num) {
  return (num ?? 0).toLocaleString();
}

// ✅ Toast for user notifications
function showToast(message) {
  const toastEl = document.getElementById('toast');
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 3000);
}

// ✅ Realtime sync with Supabase channels
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
            .channel(`kr-resources-${kid}`)
            .on('postgres_changes', {
              event: '*',
              schema: 'public',
              table: 'kingdom_resources',
              filter: `kingdom_id=eq.${kid}`
            }, (payload) => {
              renderResourceSummary(payload.new);
              renderResourceTable(payload.new);
            })
            .subscribe();
        }

        if (aid) {
          supabase
            .channel(`kr-vault-${aid}`)
            .on('postgres_changes', {
              event: '*',
              schema: 'public',
              table: 'alliance_vault',
              filter: `alliance_id=eq.${aid}`
            }, (payload) => {
              renderVaultTable(payload.new);
            })
            .subscribe();
        }
      });
  });
}
