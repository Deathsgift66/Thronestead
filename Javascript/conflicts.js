/*
Project Name: Kingmakers Rise Frontend
File Name: conflicts.js
Updated: July 2025
Description: Handles fetching and rendering kingdom and alliance wars on the
conflicts page.
*/

import { supabase } from './supabaseClient.js';

// Initialize after DOM ready
document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  setupTabs();
  await fetchKingdomWars();
  await fetchAllianceWars();
});

// Switch between Kingdom and Alliance tabs
function setupTabs() {
  const buttons = document.querySelectorAll('.tab');
  const panels = document.querySelectorAll('.tab-panel');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const panel = document.getElementById(btn.dataset.tab);
      if (panel) panel.classList.add('active');
    });
  });
}

// Load wars where the user’s kingdom is involved
export async function fetchKingdomWars() {
  const container = document.getElementById('kingdomWarsList');
  if (!container) return;
  container.innerHTML = '<p>Loading wars…</p>';
  try {
    const res = await fetch('/api/conflicts/kingdom');
    const data = await res.json();
    container.innerHTML = '';
    (data.wars || []).forEach(war => {
      const card = document.createElement('div');
      card.className = 'war-card';
      card.innerHTML = `
        <h4>${escapeHTML(war.attacker_name)} vs ${escapeHTML(war.defender_name)}</h4>
        <p>Phase: <strong>${escapeHTML(war.phase || '')}</strong></p>
        <p>Score: ${escapeHTML(war.attacker_score ?? 0)} - ${escapeHTML(war.defender_score ?? 0)}</p>
        <button class="view-war-btn" data-id="${war.war_id}">View Details</button>
      `;
      container.appendChild(card);
    });
    container.querySelectorAll('.view-war-btn').forEach(btn => {
      btn.addEventListener('click', () => fetchWarDetails(btn.dataset.id));
    });
  } catch (err) {
    console.error('Error loading kingdom wars:', err);
    container.innerHTML = '<p>Failed to load wars.</p>';
  }
}

// Load alliance level wars
export async function fetchAllianceWars() {
  const container = document.getElementById('allianceWarsList');
  if (!container) return;
  container.innerHTML = '<p>Loading wars…</p>';
  try {
    const res = await fetch('/api/conflicts/alliance');
    const data = await res.json();
    container.innerHTML = '';
    (data.wars || []).forEach(war => {
      const card = document.createElement('div');
      card.className = 'war-card';
      card.innerHTML = `
        <h4>${escapeHTML(war.attacker_alliance)} vs ${escapeHTML(war.defender_alliance)}</h4>
        <p>Phase: <strong>${escapeHTML(war.phase || '')}</strong></p>
        <p>Score: ${escapeHTML(war.attacker_score ?? 0)} - ${escapeHTML(war.defender_score ?? 0)}</p>
        <button class="view-war-btn" data-id="${war.war_id}">View Details</button>
      `;
      container.appendChild(card);
    });
    container.querySelectorAll('.view-war-btn').forEach(btn => {
      btn.addEventListener('click', () => fetchWarDetails(btn.dataset.id));
    });
  } catch (err) {
    console.error('Error loading alliance wars:', err);
    container.innerHTML = '<p>Failed to load wars.</p>';
  }
}

// Fetch full war details and display in modal
export async function fetchWarDetails(id) {
  const modal = document.getElementById('war-detail-modal');
  if (!modal) return;
  modal.innerHTML = '<div class="modal-content"><p>Loading…</p></div>';
  modal.classList.remove('hidden');
  try {
    const res = await fetch(`/api/conflicts/war/${id}/details`);
    const data = await res.json();
    modal.innerHTML = `
      <div class="modal-content">
        <h3>${escapeHTML(data.attacker_name)} vs ${escapeHTML(data.defender_name)}</h3>
        <p>Result: ${escapeHTML(data.result || 'Ongoing')}</p>
        <div id="combat-log-timeline"></div>
        <button class="close-btn">Close</button>
      </div>
    `;
    modal.querySelector('.close-btn').addEventListener('click', () => modal.classList.add('hidden'));
  } catch (err) {
    console.error('Error loading war details:', err);
    modal.innerHTML = '<div class="modal-content"><p>Failed to load details.</p><button class="close-btn">Close</button></div>';
    modal.querySelector('.close-btn').addEventListener('click', () => modal.classList.add('hidden'));
  }
}

// Utility to escape user-supplied data
function escapeHTML(str) {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
