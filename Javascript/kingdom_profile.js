// Comment
// Project Name: Thronestead©
// File Name: kingdom_profile.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { authFetchJson } from './fetchJson.js';

let targetKingdomId = null;
let currentSession = null;
let lastAction = 0;
let reportTextarea;
let reportModal;

document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(window.location.search);
  targetKingdomId = parseInt(params.get('id') || params.get('kingdom_id'), 10);
  if (!targetKingdomId) {
    document.getElementById('profile-container').innerHTML = '<p>Invalid kingdom.</p>';
    return;
  }

  const { data: { session } } = await supabase.auth.getSession();
  currentSession = session;

  await loadProfile();
  setupSpyControls();
  setupMessageButton();
  setupReportControls();
});

async function loadProfile() {
  const kNameEl = document.getElementById('kingdom-name');
  const mottoEl = document.getElementById('kingdom-motto');
  const avatarEl = document.getElementById('profile-picture');
  const rulerEl = document.getElementById('ruler-name');
  const prestigeEl = document.getElementById('prestige');
  const militaryEl = document.getElementById('military-score');
  const economyEl = document.getElementById('economy-score');
  const diplomacyEl = document.getElementById('diplomacy-score');
  const villagesEl = document.getElementById('village-count');

  kNameEl.textContent = 'Loading...';

  try {
    const res = await fetch(`/api/kingdoms/public/${targetKingdomId}`);
    const data = await res.json();

    kNameEl.textContent = data.kingdom_name || 'Unknown Kingdom';
    mottoEl.textContent = data.motto ? `"${data.motto}"` : '';
    rulerEl.textContent = data.ruler_name || '';
    avatarEl.src = data.profile_picture_url || '/Assets/avatars/default_avatar_emperor.png';
    prestigeEl.textContent = data.prestige ? `Prestige: ${data.prestige}` : '';
    militaryEl.textContent = `Military: ${data.military_score}`;
    economyEl.textContent = `Economy: ${data.economy_score}`;
    diplomacyEl.textContent = `Diplomacy: ${data.diplomacy_score}`;
    villagesEl.textContent = `Villages: ${data.village_count}`;

    if (currentSession) {
      document.getElementById('spy-btn').classList.remove('hidden');
      document.getElementById('message-btn').classList.remove('hidden');
      document.getElementById('report-btn').classList.remove('hidden');
    }
  } catch (err) {
    console.error('profile load failed', err);
    kNameEl.textContent = 'Failed to load';
  }
}

function setupSpyControls() {
  const btn = document.getElementById('spy-btn');
  const modal = document.getElementById('spy-modal');
  const closeBtn = document.getElementById('close-spy-modal');
  const attackBtn = document.getElementById('attack-modal-btn');

  if (btn) {
    btn.addEventListener('click', () => {
      modal.classList.remove('hidden');
      modal.setAttribute('aria-hidden', 'false');
    });
  }
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      modal.classList.add('hidden');
      modal.setAttribute('aria-hidden', 'true');
    });
  }

  document.querySelectorAll('.spy-option').forEach(el => {
    el.addEventListener('click', () => launchMission(el.dataset.mission));
  });

  if (attackBtn) attackBtn.addEventListener('click', confirmAttack);
}

function setupMessageButton() {
  const msgBtn = document.getElementById('message-btn');
  if (msgBtn) {
    msgBtn.addEventListener('click', () => {
      window.location.href = `compose.html?recipient=${targetKingdomId}`;
    });
  }
}

function setupReportControls() {
  reportModal = document.getElementById('report-modal');
  reportTextarea = document.getElementById('report-text');
  const btn = document.getElementById('report-btn');
  const submitBtn = document.getElementById('submit-report-btn');
  const closeBtn = document.getElementById('close-report-btn');

  if (btn) {
    btn.addEventListener('click', () => {
      if (!currentSession) return alert('Login required');
      reportModal.classList.remove('hidden');
      reportModal.setAttribute('aria-hidden', 'false');
      if (reportTextarea) reportTextarea.value = '';
    });
  }
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      reportModal.classList.add('hidden');
      reportModal.setAttribute('aria-hidden', 'true');
    });
  }
  if (submitBtn) {
    submitBtn.addEventListener('click', submitReport);
  }
}

async function launchMission(missionType) {
  if (!currentSession) return alert('Login required');
  const now = Date.now();
  if (now - lastAction < 5000) {
    alert('Please wait before launching another mission.');
    return;
  }
  lastAction = now;

  try {
    await authFetchJson('/api/kingdom/spy_missions', currentSession, {
      method: 'POST',
      body: JSON.stringify({
        target_id: targetKingdomId,
        mission_type: missionType
      })
    });
    alert(`Mission launched: ${missionType}`);
  } catch (err) {
    alert(`❌ Mission failed: ${err.message}`);
  } finally {
    document.getElementById('spy-modal').classList.add('hidden');
    document.getElementById('spy-modal').setAttribute('aria-hidden', 'true');
  }
}

async function confirmAttack() {
  if (!currentSession) return alert('Login required');
  if (!window.confirm('⚔️ Are you sure you want to declare war on this kingdom?')) return;

  try {
    const result = await authFetchJson('/api/wars/declare', currentSession, {
      method: 'POST',
      body: JSON.stringify({ target: targetKingdomId })
    });
    if (result.success && result.war_id) {
      window.location.href = `/battle_live.html?war_id=${result.war_id}`;
    } else {
      alert(`❌ Attack failed: ${result.message || 'Unknown error'}`);
    }
  } catch (err) {
    alert(`❌ Attack failed: ${err.message}`);
  }
}

async function submitReport() {
  if (!currentSession) return alert('Login required');
  const desc = reportTextarea?.value.trim();
  if (!desc) {
    alert('Please provide a reason for your report.');
    return;
  }

  try {
    await authFetchJson('/api/reports/submit', currentSession, {
      method: 'POST',
      body: JSON.stringify({
        category: 'player',
        description: desc,
        target_id: String(targetKingdomId)
      })
    });
    alert('Report submitted. False claims may lead to penalties.');
  } catch (err) {
    alert(`❌ Report failed: ${err.message}`);
  } finally {
    reportModal.classList.add('hidden');
    reportModal.setAttribute('aria-hidden', 'true');
  }
}
