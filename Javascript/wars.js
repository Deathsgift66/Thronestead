// Project Name: Thronestead©
// File Name: wars.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Unified War Command Center — Page Controller
import { escapeHTML } from './utils.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';
import { supabase } from '../supabaseClient.js';

let lastWarDate = null;

document.addEventListener('DOMContentLoaded', async () => {
  setupControls();
  subscribeToWarUpdates();
  await loadWars();
  showToast('Unified War Command Center loaded!');
  applyKingdomLinks();
});

// Setup Page Controls
function setupControls() {
  const declareWarBtn = document.getElementById('declareWarButton');
  if (declareWarBtn) {
    declareWarBtn.addEventListener('click', openDeclareWarModal);
  }

  const form = document.getElementById('declare-war-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await submitDeclareWar();
    });
  }

  const cancelBtn = document.getElementById('declare-war-cancel');
  if (cancelBtn) cancelBtn.addEventListener('click', closeDeclareWarModal);

  const refreshWarsBtn = document.getElementById('refreshWarsButton');
  if (refreshWarsBtn) {
    refreshWarsBtn.addEventListener('click', async () => {
      showToast('Refreshing active wars...');
      await loadWars();
    });
  }

  const loadMoreBtn = document.getElementById('load-more-wars-btn');
  if (loadMoreBtn) loadMoreBtn.addEventListener('click', () => loadWars(true));
}

// Subscribe to Supabase real-time updates
function subscribeToWarUpdates() {
  supabase
    .channel('public:wars')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'wars' }, async payload => {
      if (payload.new) {
        appendWarEvent(`${escapeHTML(payload.new.attacker_name)} vs ${escapeHTML(payload.new.defender_name)} — ${escapeHTML(payload.new.status)}`);
      }
      await loadWars();
    })
    .on('error', (e) => {
      console.error('Supabase RT error:', e);
      showToast('Realtime war feed failed.');
    })
    .on('close', () => {
      showToast('Realtime war feed closed.');
    })
    .subscribe();
}

// Append a new event message at the top of war feed
function appendWarEvent(msg) {
  const feed = document.getElementById('war-feed');
  if (!feed) return;
  const el = document.createElement('div');
  el.className = 'war-event';
  el.textContent = msg;
  feed.prepend(el);
  if (feed.children.length > 50) feed.removeChild(feed.lastChild);
}

// Load Active Wars
async function loadWars(append = false) {
  const warListEl = document.getElementById('war-list');
  if (!append) {
    warListEl.innerHTML = '<p>Loading active wars...</p>';
    lastWarDate = null;
  }

  try {
    let query = supabase
      .from('wars')
      .select('*')
      .order('start_date', { descending: true })
      .limit(25);
    if (append && lastWarDate) {
      query = query.lt('start_date', lastWarDate);
    }
    const { data: wars, error } = await query;

    if (error) throw error;

    if (!append) warListEl.innerHTML = '';

    if (wars.length === 0) {
      if (!append) warListEl.innerHTML = '<p>No active wars at this time.</p>';
      document.getElementById('load-more-wars-btn')?.classList.add('hidden');
      return;
    }

    wars.forEach(war => {
      const card = document.createElement('div');
      card.classList.add('war-card');
      card.innerHTML = `
        <h3>${escapeHTML(war.attacker_name)} ⚔️ ${escapeHTML(war.defender_name)}</h3>
        <p class="war-reason">${escapeHTML(war.war_reason || '')}</p>
        <p>Status: ${escapeHTML(war.status)}</p>
        <p>Start: ${new Date(war.start_date).toLocaleString()}</p>
        <p>Score: ${war.attacker_score} - ${war.defender_score}</p>
      `;

      const btn = document.createElement('button');
      btn.className = 'action-btn';
      btn.textContent = 'View Details';
      btn.addEventListener('click', () => openWarDetailModal(war.war_id));
      card.appendChild(btn);

      warListEl.appendChild(card);
    });

    lastWarDate = wars[wars.length - 1].start_date;
    const moreBtn = document.getElementById('load-more-wars-btn');
    if (moreBtn) {
      if (wars.length === 25) {
        moreBtn.classList.remove('hidden');
      } else {
        moreBtn.classList.add('hidden');
      }
    }

  } catch (err) {
    console.error('❌ Error loading wars:', err);
    warListEl.innerHTML = '<p>Failed to load active wars.</p>';
    showToast('Failed to load wars.');
  }
  applyKingdomLinks();
}

// Open Declare War Modal
function openDeclareWarModal() {
  const modal = document.getElementById('declare-war-modal');
  if (modal) modal.classList.remove('hidden');
}

// Close Declare War Modal
function closeDeclareWarModal() {
  const modal = document.getElementById('declare-war-modal');
  if (modal) modal.classList.add('hidden');
}

// Submit Declare War
async function submitDeclareWar() {
  const targetInput = document.getElementById('target-kingdom-id');
  const reasonInput = document.getElementById('war-reason');
  const rawTargetId = targetInput?.value.trim();
  const targetId = parseInt(rawTargetId, 10);
  const reason = reasonInput?.value.trim();

  if (!rawTargetId || !reason) {
    showToast('Please fill in all fields.');
    return;
  }

  if (isNaN(targetId) || targetId <= 0) {
    showToast('Invalid target kingdom ID.');
    return;
  }

  if (!/^[\\w\\s.,'’\\-]{5,100}$/.test(reason)) {
    showToast('Invalid war reason format.');
    return;
  }

  const declareBtn = document.querySelector('#declare-war-form button[type="submit"]');
  if (declareBtn) {
    declareBtn.disabled = true;
    setTimeout(() => { declareBtn.disabled = false; }, 3000);
  }

  let session;
  try {
    const { data } = await supabase.auth.getSession();
    session = data?.session;
    if (!session || !session.user) throw new Error();
  } catch {
    showToast('Unable to verify session. Please log in.');
    return;
  }

  try {
    const res = await fetch('/api/wars/declare', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        target: targetId,
        war_reason: reason
      })
    });

    const result = await res.json();

    if (!res.ok) throw new Error(result.error || 'Failed to declare war.');

    showToast('War declared successfully!');
    closeDeclareWarModal();
    await loadWars();

  } catch (err) {
    console.error('❌ Error declaring war:', err);
    showToast('Failed to declare war.');
  }
}

// Open War Detail Modal
async function openWarDetailModal(warId) {
  if (!warId || typeof warId !== 'number') {
    showToast('Invalid war ID.');
    return;
  }
  const modal = document.getElementById('war-detail-modal');
  if (!modal) return;

  modal.classList.remove('hidden');
  const content = modal.querySelector('.modal-content');
  if (!content) return;
  content.innerHTML = `<h3>War Details</h3><p>Loading war details...</p><button type="button" class="action-btn" id="war-detail-close">Close</button>`;

  const closeBtn = content.querySelector('#war-detail-close');
  closeBtn.addEventListener('click', closeWarDetailModal);

  try {
    const res = await fetch(`/api/wars/view?war_id=${warId}`);
    if (!res.ok) throw new Error('Failed to load war details');
    const { war } = await res.json();

    content.innerHTML = `
      <h3>${escapeHTML(war.attacker_name)} ⚔️ ${escapeHTML(war.defender_name)}</h3>
      <p>Status: ${escapeHTML(war.status)}</p>
      <p>Start Date: ${new Date(war.start_date).toLocaleString()}</p>
      <p>Score: ${war.attacker_score} - ${war.defender_score}</p>
      <p>Reason: ${escapeHTML(war.war_reason || 'Unknown')}</p>
      <button type="button" class="action-btn" id="war-detail-close-btn">Close</button>
    `;

    content.querySelector('#war-detail-close-btn').addEventListener('click', closeWarDetailModal);
    applyKingdomLinks();

  } catch (err) {
    console.error('❌ Error loading war details:', err);
    showToast('Failed to load war details.');
  }
}

// Close War Detail Modal
function closeWarDetailModal() {
  const modal = document.getElementById('war-detail-modal');
  if (modal) modal.classList.add('hidden');
}

// Toast Helper
function showToast(msg) {
  let toastEl = document.getElementById('toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.id = 'toast';
    toastEl.className = 'toast-notification';
    toastEl.setAttribute('role', 'status');
    toastEl.setAttribute('aria-live', 'polite');
    document.body.appendChild(toastEl);
  }

  toastEl.textContent = msg;
  toastEl.classList.add('show');

  setTimeout(() => {
    toastEl.classList.remove('show');
  }, 3000);
}
