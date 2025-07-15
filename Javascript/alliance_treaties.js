// Project Name: Thronestead©
// File Name: alliance_treaties.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { escapeHTML, openModal, closeModal } from './utils.js';

// Fallbacks if utils.js didn't define them
if (typeof openModal !== 'function') {
  window.openModal = id => {
    const el = document.getElementById(id);
    el?.classList.remove('hidden');
    el?.focus();
  };
}
if (typeof closeModal !== 'function') {
  window.closeModal = id => {
    document.getElementById(id)?.classList.add('hidden');
  };
}

// -------------------- Initialization --------------------

document.addEventListener('DOMContentLoaded', () => {

  loadTreaties();
  document.getElementById('create-new-treaty')?.addEventListener('click', proposeTreaty);
  document.getElementById('propose-treaty-form')?.addEventListener('submit', submitProposeTreaty);
  document.getElementById('cancel-propose-treaty')?.addEventListener('click', closeProposeTreatyModal);
  document.getElementById('propose-treaty-modal')?.addEventListener('click', e => {
    if (e.target.id === 'propose-treaty-modal') closeProposeTreatyModal();
  });
  document.querySelector('.modal-close')?.addEventListener('click', () => closeModal('treaty-modal'));
  document.getElementById('treaty-modal')?.addEventListener('click', e => {
    if (e.target.id === 'treaty-modal') closeModal('treaty-modal');
  });
});

// -------------------- Treaty Feed --------------------

async function loadTreaties() {
  const container = document.getElementById('treaties-container');
  container.innerHTML = '<p>Loading treaties...</p>';
  try {
    const res = await fetch('/api/alliance/treaties');
    const treaties = await res.json();
    if (!treaties.length) {
      container.innerHTML = "<p class='empty-state'>No treaties found.</p>";
      return;
    }
    container.innerHTML = treaties.map(t => renderTreatyCard(t)).join('');
    bindCardActions();
  } catch (err) {
    console.error('Failed to load treaties:', err);
    container.innerHTML = '<p>Failed to load treaties.</p>';
  }
}

function renderTreatyCard(t) {
  const type = (t.type || t.treaty_type || '').replaceAll('_', ' ').toUpperCase();
  return `
    <div class="treaty-card ${t.status}">
      <h3>${escapeHTML(type)}</h3>
      <p><strong>With:</strong> ${escapeHTML(t.partner_name)}</p>
      <p><strong>Status:</strong> ${escapeHTML(t.status)}</p>
      ${t.status === 'proposed' ? "<button class='respond-btn' data-id='" + t.treaty_id + "'>Respond</button>" : ''}
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

// -------------------- Modal --------------------

function openTreatyModal(id) {
  fetch(`/api/alliance/treaty/${id}`)
    .then(res => res.json())
    .then(t => {
      const box = document.getElementById('treaty-details');
      const termsRows = Object.entries(t.terms || {}).length
        ? Object.entries(t.terms)
            .map(
              ([k, v]) =>
                `<tr><th>${escapeHTML(k)}</th><td>${escapeHTML(String(v))}</td></tr>`
            )
            .join('')
        : '<tr><td colspan="2">No terms listed.</td></tr>';
      box.innerHTML = `
        <h3>${escapeHTML(t.name)}</h3>
        <p>Partner: ${escapeHTML(t.partner_name)}</p>
        <p>Status: ${escapeHTML(t.status)}</p>
        <table class="terms-table"><tbody>${termsRows}</tbody></table>
        ${t.status === 'proposed' ? `
          <button class="accept-btn" data-id="${t.treaty_id}">Accept</button>
          <button class="reject-btn" data-id="${t.treaty_id}">Reject</button>
        ` : ''}
      `;
      openModal('treaty-modal');
      document.querySelector('.accept-btn')?.addEventListener('click', () => respondToTreaty(t.treaty_id, 'accept'));
      document.querySelector('.reject-btn')?.addEventListener('click', () => respondToTreaty(t.treaty_id, 'reject'));
    })
    .catch(err => console.error('Failed to load treaty:', err));
}

// -------------------- Actions --------------------

async function respondToTreaty(id, response) {
  try {
    await fetch('/api/alliance/treaties/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ treaty_id: parseInt(id, 10), response })
    });
    closeModal('treaty-modal');
    loadTreaties();
  } catch (err) {
    console.error('Failed to respond:', err);
  }
}

function proposeTreaty() {
  openModal('propose-treaty-modal');
}

function closeProposeTreatyModal() {
  closeModal('propose-treaty-modal');
}

async function submitProposeTreaty(event) {
  event.preventDefault();
  const type = document.getElementById('treaty-type')?.value;
  const partnerId = document.getElementById('partner-alliance-id')?.value;
  if (!type || !partnerId) return;
  try {
    await fetch('/api/alliance/treaties/propose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        partner_alliance_id: parseInt(partnerId, 10),
        treaty_type: type,
        terms: { duration_days: 30, exclusive: true }
      })
    });
    closeProposeTreatyModal();
    loadTreaties();
  } catch (err) {
    console.error('Failed to propose treaty:', err);
  }
}
