// Project Name: Thronestead©
// File Name: alliance_vault.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { RESOURCE_TYPES } from './resourceTypes.js';
import { loadCustomBoard } from './customBoard.js';
import { escapeHTML, authFetch } from './utils.js';
import { setupTabs } from './components/tabControl.js';

let currentUser = null;
const feedbackEl = document.getElementById('vault-message');
function showFeedback(msg) {
  if (!feedbackEl) {
    alert(msg);
    return;
  }
  feedbackEl.textContent = msg;
  feedbackEl.scrollIntoView({ behavior: 'smooth' });
  setTimeout(() => {
    if (feedbackEl.textContent === msg) feedbackEl.textContent = '';
  }, 4000);
}
let currentFilters = { action: '', days: '' };

function subscribeToVault(allianceId) {
  supabase
    .channel(`vault_${allianceId}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'alliance_vault_transaction_log',
        filter: `alliance_id=eq.${allianceId}`
      },
      async () => {
        await loadVaultSummary();
        await loadTransactions();
      }
    )
    .subscribe();
}

document.addEventListener('DOMContentLoaded', async () => {
  const {
    data: { user }
  } = await supabase.auth.getUser();
  if (!user) return (window.location.href = 'login.html');
  currentUser = user;

  setupTabs({
    onShow: id => {
      if (id === 'tab-transactions') {
        loadTransactions(currentFilters.action, currentFilters.days);
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
      } else if (id === 'tab-manage') {
        document.getElementById('vault-message')?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });
  await Promise.all([
    loadVaultSummary(),
    loadCustomBoard({ endpoint: '/api/alliance/custom/vault', fetchFn: authFetch }),
    loadDepositForm(),
    loadWithdrawForm(),
    loadTransactions()
  ]);

  const { data: allianceData } = await supabase
    .from('users')
    .select('alliance_id')
    .eq('user_id', user.id)
    .single();

  if (allianceData?.alliance_id) {
    subscribeToVault(allianceData.alliance_id);
  }

  try {
    const res = await authFetch('/api/alliance-members/view');
    const json = await res.json();
    const me = (json.alliance_members || []).find(m => m.user_id === currentUser.id);
    if (!me || !(me.can_manage_resources || me.permissions?.can_manage_resources)) {
      document.getElementById('withdraw-section').style.display = 'none';
    }
  } catch (err) {
    console.error('Permission check failed:', err);
  }

  document.getElementById('apply-trans-filter')?.addEventListener('click', () => {
    currentFilters.action = document.getElementById('filter-action')?.value || '';
    currentFilters.days = document.getElementById('filter-days')?.value || '';
    loadTransactions(currentFilters.action, currentFilters.days);
  });
});

function renderVaultSummary(data) {
  const container = document.querySelector('.vault-summary');
  container.innerHTML = Object.entries(data)
    .map(([key, value]) => {
      const label = escapeHTML(key.replaceAll('_', ' '));
      return `
      <div class="progress-bar">
        <label>${label}</label>
        <progress value="${value}" max="${value}"></progress>
        <span>${value.toLocaleString()}</span>
      </div>
    `;
    })
    .join('');
}

async function loadVaultSummary() {
  const container = document.querySelector('.vault-summary');
  container.innerHTML = '<p>Loading vault totals...</p>';
  try {
    const res = await authFetch('/api/vault/resources');
    const { totals } = await res.json();
    if (!totals || Object.keys(totals).length === 0) {
      container.innerHTML = '<p>No resources in vault.</p>';
      return;
    }
    renderVaultSummary(totals);
  } catch (err) {
    console.error('❌ Vault Summary:', err);
    container.innerHTML = '<p>Failed to load vault totals.</p>';
  }
}

function buildResourceInputForm(type, containerId) {
  const container = document.getElementById(containerId);
  if (!Array.isArray(RESOURCE_TYPES) || !RESOURCE_TYPES.length) {
    container.innerHTML = '<p>Failed to load resource types.</p>';
    return;
  }
  container.innerHTML = `
    <form id="${type}-form" class="resource-form" data-testid="${type}-form">
      ${RESOURCE_TYPES.map(
        r => `
        <div class="resource-input-row">
          <label>${r}</label>
          <input type="number" min="0" name="${r}" data-type="${type}" data-testid="${type}-${r.replace(/\s+/g, '-')}-input" />
        </div>
      `
      ).join('')}
      <button class="action-btn" type="submit">${type === 'deposit' ? 'Deposit' : 'Withdraw'}</button>
    </form>
  `;

  document.getElementById(`${type}-form`).addEventListener('submit', async e => {
    e.preventDefault();
    const inputs = Array.from(
      document.querySelectorAll(`#${type}-form input[data-type='${type}']`)
    );
    const payloads = inputs
      .map(i => ({ res: i.name.toLowerCase().replace(/ /g, '_'), amt: parseInt(i.value) || 0 }))
      .filter(p => p.amt > 0);
    if (!payloads.length) return showFeedback('Enter amounts.');
    for (const p of payloads) {
      if (type === 'withdraw' && p.amt > 1000) {
        if (!confirm(`Withdraw ${p.amt} ${p.res}?`)) continue;
      }
      try {
        await authFetch(`/api/alliance/vault/${type}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ resource: p.res, amount: p.amt })
        });
      } catch (err) {
        console.error(`❌ ${type}:`, err);
      }
    }
    await loadVaultSummary();
    await loadTransactions();
    inputs.forEach(i => {
      i.value = '';
    });
    showFeedback(`${type.charAt(0).toUpperCase() + type.slice(1)} complete.`);
  });
}

function loadDepositForm() {
  buildResourceInputForm('deposit', 'deposit-section');
}

function loadWithdrawForm() {
  buildResourceInputForm('withdraw', 'withdraw-section');
}

async function loadTransactions(action = '', days = '') {
  const tbody = document.getElementById('vault-history');
  tbody.innerHTML = `<tr><td colspan="6">Loading...</td></tr>`;

  try {
    const params = new URLSearchParams();
    action = action || document.getElementById('filter-action')?.value || '';
    days = days || document.getElementById('filter-days')?.value || '';
    if (action) params.append('action', action);
    if (days) params.append('days', days);

    const res = await authFetch(`/api/alliance/vault/transactions?${params}`);
    const logs = await res.json();
    const history = logs || [];

    tbody.innerHTML = '';
    if (!history.length) {
      tbody.innerHTML = `<tr><td colspan="6">No transactions found.</td></tr>`;
      return;
    }

    history.forEach(log => {
      const row = document.createElement('tr');
      const ts = new Date(log.timestamp || log.created_at);
      row.innerHTML = `
        <td><time datetime="${ts.toISOString()}" data-testid="transaction-time">${ts.toLocaleString()}</time></td>
        <td>${escapeHTML(log.user || log.username || log.user_id || 'System')}</td>
        <td>${escapeHTML(log.action)}</td>
        <td>${escapeHTML(log.resource_type)}</td>
        <td>${log.amount}</td>
        <td>${escapeHTML(log.notes || '-')}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error('❌ Vault History:', err);
    tbody.innerHTML = `<tr><td colspan="6">Failed to load history.</td></tr>`;
  }
}
