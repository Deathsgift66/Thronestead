// Project Name: Thronestead©
// File Name: alliance_treaties.js
// Version 6.30.2025
// Developer: Codex
import { escapeHTML } from './utils.js';

// -------------------- Initialization --------------------

document.addEventListener('DOMContentLoaded', () => {

  loadTreaties();
  document.getElementById('create-new-treaty')?.addEventListener('click', proposeTreaty);
  document.querySelector('.modal-close')?.addEventListener('click', closeModal);
  document.getElementById('treaty-modal')?.addEventListener('click', e => {
    if (e.target.id === 'treaty-modal') closeModal();
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
      box.innerHTML = `
        <h3>${escapeHTML(t.name)}</h3>
        <p>Partner: ${escapeHTML(t.partner_name)}</p>
        <p>Status: ${escapeHTML(t.status)}</p>
        <p>Terms: ${escapeHTML(JSON.stringify(t.terms))}</p>
        ${t.status === 'proposed' ? `
          <button class="accept-btn" data-id="${t.id}">Accept</button>
          <button class="reject-btn" data-id="${t.id}">Reject</button>
        ` : ''}
      `;
      const modal = document.getElementById('treaty-modal');
      modal.classList.remove('hidden');
      modal.setAttribute('aria-hidden', 'false');
      document.querySelector('.accept-btn')?.addEventListener('click', () => respondToTreaty(t.id, 'accept'));
      document.querySelector('.reject-btn')?.addEventListener('click', () => respondToTreaty(t.id, 'reject'));
    })
    .catch(err => console.error('Failed to load treaty:', err));
}

function closeModal() {
  const modal = document.getElementById('treaty-modal');
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
}

// -------------------- Actions --------------------

async function respondToTreaty(id, response) {
  try {
    await fetch('/api/alliance/treaties/respond', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ treaty_id: parseInt(id, 10), response })
    });
    closeModal();
    loadTreaties();
  } catch (err) {
    console.error('Failed to respond:', err);
  }
}

async function proposeTreaty() {
  const type = prompt('Enter treaty type (non_aggression_pact, defensive_pact, trade_pact, intelligence_sharing, research_collaboration):');
  const partnerId = prompt('Enter partner alliance ID:');
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
    loadTreaties();
  } catch (err) {
    console.error('Failed to propose treaty:', err);
  }
}
