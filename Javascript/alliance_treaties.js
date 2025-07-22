// Project Name: Thronestead©
// File Name: alliance_treaties.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { escapeHTML, openModal, closeModal, authFetch, showToast, toggleLoading } from './utils.js';
import './modalFallback.js';
import { initCsrf, getCsrfToken, rotateCsrfToken } from './security/security.js';

initCsrf();
setInterval(rotateCsrfToken, 15 * 60 * 1000);

// -------------------- Initialization --------------------
let lastFocused = null;
let treatyChannel = null;
let submitting = false;
let pendingResponse = null;
let userHasTreatyPermission = false;
let alliances = [];
const STATUS_ICONS = { proposed: '⏳', active: '✅', cancelled: '❌', expired: '⌛' };

document.addEventListener('DOMContentLoaded', () => {
  loadTreaties();
  subscribeToRealtime();
  checkTreatyPermission();
  fetchAlliances();
  document.getElementById('create-new-treaty')?.addEventListener('click', proposeTreaty);
  const filterBox = document.getElementById('filter-active');
  if (filterBox) {
    const saved = sessionStorage.getItem('filterActive');
    if (saved !== null) filterBox.checked = saved === '1';
    filterBox.addEventListener('change', e => {
      sessionStorage.setItem('filterActive', e.target.checked ? '1' : '0');
      loadTreaties();
    });
  }
  document.getElementById('propose-treaty-form')?.addEventListener('submit', submitProposeTreaty);
  document.getElementById('partner-alliance-name')?.addEventListener('input', e => showAllianceSuggestions(e.target.value));
  const typeSelect = document.getElementById('treaty-type');
  const typeDesc = document.getElementById('treaty-type-desc');
  if (typeSelect && typeDesc) {
    const updateDesc = () => {
      const opt = typeSelect.options[typeSelect.selectedIndex];
      typeDesc.textContent = opt?.title || '';
    };
    typeSelect.addEventListener('change', updateDesc);
    updateDesc();
  }
  document.getElementById('cancel-propose-treaty')?.addEventListener('click', closeProposeTreatyModal);
  document.getElementById('propose-treaty-modal')?.addEventListener('click', e => {
    if (e.target.id === 'propose-treaty-modal') closeProposeTreatyModal();
  });
  document.querySelector('.modal-close')?.addEventListener('click', closeTreatyModal);
  document.getElementById('treaty-modal')?.addEventListener('click', e => {
    if (e.target.classList.contains('accept-btn')) {
      respondToTreaty(e.target.dataset.id, 'accept');
    } else if (e.target.classList.contains('reject-btn')) {
      respondToTreaty(e.target.dataset.id, 'reject');
    } else if (e.target.classList.contains('cancel-btn')) {
      cancelTreaty(e.target.dataset.id);
    } else if (e.target.id === 'treaty-modal') {
      closeTreatyModal();
    }
  });
  document.getElementById('respond-yes')?.addEventListener('click', () => {
    closeModal('respond-confirm-modal');
    pendingResponse?.();
    pendingResponse = null;
  });
  document.getElementById('respond-no')?.addEventListener('click', () => {
    closeModal('respond-confirm-modal');
    pendingResponse = null;
    lastFocused?.focus();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      if (!document.getElementById('treaty-modal').classList.contains('hidden')) {
        closeTreatyModal();
      } else if (!document.getElementById('propose-treaty-modal').classList.contains('hidden')) {
        closeProposeTreatyModal();
      } else if (!document.getElementById('respond-confirm-modal').classList.contains('hidden')) {
        closeModal('respond-confirm-modal');
        pendingResponse = null;
        lastFocused?.focus();
      }
    } else if (e.altKey && e.key.toLowerCase() === 'n') {
      if (document.getElementById('propose-treaty-modal').classList.contains('hidden')) {
        e.preventDefault();
        proposeTreaty();
      }
    }
  });
});

// -------------------- Treaty Feed --------------------
async function loadTreaties() {
  const container = document.getElementById('treaties-container');
  container.innerHTML = '<p>Loading treaties...</p>';
  try {
    const res = await authFetch('/api/alliance/treaties');
    if (res.status === 401) {
      window.location.href = 'login.html';
      return;
    }
    const treaties = await res.json();
    const onlyActive = document.getElementById('filter-active')?.checked;
    const filtered = onlyActive ? treaties.filter(t => t.status === 'active') : treaties;
    if (!filtered.length) {
      container.innerHTML = "<p class='empty-state'>No treaties found.</p>";
      return;
    }
    container.innerHTML = filtered.map(t => renderTreatyCard(t)).join('');
    container.classList.remove('fade-in');
    void container.offsetWidth;
    container.classList.add('fade-in');
    bindCardActions();
  } catch (err) {
    console.error('Failed to load treaties:', err);
    container.innerHTML = '<p>Failed to load treaties.</p>';
    showToast('Failed to load treaties.', 'error');
  }
}

function renderTreatyCard(t) {
  const rawType = t.type || t.treaty_type || '';
  const type = rawType.replaceAll('_', ' ').toUpperCase();
  const icons = {
    non_aggression_pact: '🕊',
    defensive_pact: '🛡',
    trade_pact: '⚔',
    intelligence_sharing: '⚔',
    research_collaboration: '🕊'
  };
  const icon = icons[rawType] || '';
  const statusIcon = STATUS_ICONS[t.status] || '';
  return `
        <div class="treaty-card ${t.status}">
          <h3>${icon} ${escapeHTML(type)}</h3>
          <p><strong>With:</strong> ${escapeHTML(t.partner_name)}</p>
          <p><strong>Status:</strong> <span class="status-icon">${statusIcon}</span>${escapeHTML(t.status)}</p>
          ${
            t.status === 'proposed'
              ? "<button class='respond-btn' data-id='" + t.treaty_id + "'>Respond</button>"
              : ''
          }
          <button class="view-btn" data-id="${t.treaty_id}">View</button>
        </div>
      `;
}

function bindCardActions() {
  document.querySelectorAll('.view-btn').forEach(btn => {
    btn.addEventListener('click', () => openTreatyModal(btn.dataset.id));
  });
  document.querySelectorAll('.respond-btn').forEach(btn => {
    btn.addEventListener('click', () => openTreatyModal(btn.dataset.id));
  });
}

function closeTreatyModal() {
  closeModal('treaty-modal');
  lastFocused?.focus();
}

async function checkTreatyPermission() {
  try {
    const res = await authFetch('/api/alliance-members/view');
    const json = await res.json();
    const me = (json.alliance_members || []).find(m => m.user_id === window.user?.id);
    userHasTreatyPermission = !!(
      me && (me.permissions?.can_manage_treaties || ['Leader', 'Elder'].includes(me.role))
    );
    if (!userHasTreatyPermission) {
      document.getElementById('create-new-treaty')?.remove();
    }
  } catch (err) {
    console.error('Permission check failed:', err);
  }
}

function subscribeToRealtime() {
  if (!window.supabase) return;
  treatyChannel = window.supabase
    .channel('public:alliance_treaties')
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'alliance_treaties' },
      () => loadTreaties()
    )
    .subscribe();

  window.addEventListener('beforeunload', async () => {
    if (treatyChannel) await treatyChannel.unsubscribe();
    treatyChannel = null;
  });
  window.supabase.auth.onAuthStateChange(() => {
    if (treatyChannel) {
      treatyChannel.unsubscribe().then(() => {
        treatyChannel = null;
        subscribeToRealtime();
      });
    } else {
      subscribeToRealtime();
    }
  });
}

async function fetchAlliances() {
  try {
    const res = await fetch('/api/diplomacy/alliances');
    const data = await res.json();
    alliances = data.alliances || [];
  } catch (err) {
    console.error('Alliance list error:', err);
  }
}

function showAllianceSuggestions(query) {
  const list = document.getElementById('alliance-list');
  if (!list) return;
  list.innerHTML = '';
  if (!query) return;
  alliances
    .filter(a => a.name.toLowerCase().startsWith(query.toLowerCase()))
    .slice(0, 5)
    .forEach(a => {
      const opt = document.createElement('option');
      opt.value = a.name;
      opt.dataset.id = a.alliance_id;
      list.appendChild(opt);
    });
}

// -------------------- Modal --------------------
async function openTreatyModal(id) {
  try {
    lastFocused = document.activeElement;
    const box = document.getElementById('treaty-details');
    box.innerHTML = '<p>Loading...</p>';
    openModal('treaty-modal');
    const res = await authFetch(`/api/alliance/treaty/${id}`);
    if (!res.ok) throw new Error('Failed to fetch treaty');
    const t = await res.json();

    const termsRows = Object.entries(t.terms || {}).length
      ? Object.entries(t.terms)
          .map(([k, v]) => `<tr><th>${escapeHTML(k)}</th><td>${escapeHTML(String(v))}</td></tr>`)
          .join('')
      : '<tr><td colspan="2">No terms listed.</td></tr>';
    box.innerHTML = `
            <h3>${escapeHTML(t.name)}</h3>
            <p>Partner: ${escapeHTML(t.partner_name)}</p>
            <p>Status: <span class="status-icon">${STATUS_ICONS[t.status] || ''}</span>${escapeHTML(t.status)}</p>
            <table class="terms-table"><tbody>${termsRows}</tbody></table>
            ${
              t.status === 'proposed'
                ? `
          <button class="accept-btn" data-id="${t.treaty_id}">Accept</button>
          <button class="reject-btn" data-id="${t.treaty_id}">Reject</button>
        `
                : ''
            }
            ${
              t.status === 'active' && userHasTreatyPermission
                ? `<button class="cancel-btn" data-id="${t.treaty_id}">Cancel Treaty</button>`
                : ''
            }
          `;
  } catch (err) {
    console.error('Failed to load treaty:', err);
    showToast('Failed to load treaty details.', 'error');
  }
}

// -------------------- Actions --------------------
function respondToTreaty(id, response) {
  lastFocused = document.activeElement;
  pendingResponse = () => executeResponse(id, response);
  document.getElementById('respond-body').textContent = `Are you sure you want to ${escapeHTML(response)} this treaty?`;
  openModal('respond-confirm-modal');
}

async function executeResponse(id, response) {
  const acceptBtn = document.querySelector('.accept-btn');
  const rejectBtn = document.querySelector('.reject-btn');
  acceptBtn?.setAttribute('disabled', '');
  rejectBtn?.setAttribute('disabled', '');
  toggleLoading(true);
  try {
    const res = await authFetch('/api/alliance/treaties/respond', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken()
      },
      body: JSON.stringify({ treaty_id: parseInt(id, 10), response })
    });
    if (!res.ok) throw new Error(await res.text());
    closeTreatyModal();
    showToast('Treaty updated.', 'success');
    loadTreaties();
  } catch (err) {
    console.error('Failed to respond:', err);
    showToast('Failed to update treaty.', 'error');
  } finally {
    toggleLoading(false);
    acceptBtn?.removeAttribute('disabled');
    rejectBtn?.removeAttribute('disabled');
  }
}

async function cancelTreaty(id) {
  if (!confirm('Cancel this treaty?')) return;
  toggleLoading(true);
  try {
    const res = await authFetch('/api/alliance/treaties/cancel', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken()
      },
      body: JSON.stringify({ treaty_id: parseInt(id, 10) })
    });
    if (!res.ok) throw new Error(await res.text());
    closeTreatyModal();
    showToast('Treaty cancelled.', 'success');
    loadTreaties();
  } catch (err) {
    console.error('Failed to cancel treaty:', err);
    showToast('Failed to cancel treaty.', 'error');
  } finally {
    toggleLoading(false);
  }
}

function proposeTreaty() {
  lastFocused = document.activeElement;
  document.getElementById('create-new-treaty')?.setAttribute('aria-pressed', 'true');
  openModal('propose-treaty-modal');
}

function closeProposeTreatyModal() {
  closeModal('propose-treaty-modal');
  document.getElementById('create-new-treaty')?.setAttribute('aria-pressed', 'false');
  lastFocused?.focus();
}

async function submitProposeTreaty(event) {
  event.preventDefault();
  if (submitting) return;
  submitting = true;
  const errorBox = document.getElementById('form-error');
  if (errorBox) errorBox.textContent = '';
  const typeRaw = document.getElementById('treaty-type')?.value;
  const type = String(typeRaw || '').trim();
  const nameInput = document.getElementById('partner-alliance-name');
  const partnerName = nameInput?.value.trim();
  const list = document.getElementById('alliance-list');
  const opt = Array.from(list?.options || []).find(o => o.value === partnerName);
  if (!opt) {
    errorBox.textContent = 'Invalid alliance name.';
    submitting = false;
    return;
  }
  const partnerNum = parseInt(opt.dataset.id, 10);
  const durationVal = parseInt(document.getElementById('duration-days')?.value, 10);
  const exclusive = document.getElementById('exclusive')?.checked;
  const allowedTypes = [
    'non_aggression_pact',
    'defensive_pact',
    'trade_pact',
    'intelligence_sharing',
    'research_collaboration'
  ];
  if (
    !allowedTypes.includes(type) ||
    !partnerName ||
    !Number.isInteger(partnerNum) ||
    partnerNum <= 0 ||
    (durationVal && (!Number.isInteger(durationVal) || durationVal <= 0 || durationVal > 180))
  ) {
    errorBox.textContent = 'Invalid treaty details.';
    showToast('Invalid treaty details.', 'error');
    submitting = false;
    return;
  }
  const submitBtn = event.target.querySelector('button[type="submit"]');
  submitBtn?.setAttribute('disabled', '');
  toggleLoading(true);
  try {
    const res = await authFetch('/api/alliance/treaties/propose', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken()
      },
      body: JSON.stringify({
        partner_alliance_id: partnerNum,
        treaty_type: type,
        terms: { duration_days: durationVal || 30, exclusive: !!exclusive }
      })
    });
    if (!res.ok) throw new Error(await res.text());
    closeProposeTreatyModal();
    showToast('Treaty proposed.', 'success');
    loadTreaties();
  } catch (err) {
    console.error('Failed to propose treaty:', err);
    if (errorBox) errorBox.textContent = err.message;
    showToast('Failed to propose treaty.', 'error');
  } finally {
    toggleLoading(false);
    submitBtn?.removeAttribute('disabled');
    submitting = false;
  }
}
