// Project Name: Thronestead©
// File Name: spy_mission.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

let currentUserId = null;
let spyInfo = { spy_count: 0, spy_level: 1 };

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  currentUserId = session.user.id;

  await loadSpyInfo();

  const targetInput = document.getElementById('target-kingdom');
  targetInput.addEventListener('input', e => loadKingdomSuggestions(e.target.value));

  document.getElementById('mission-type').addEventListener('change', updateSuccessRate);
  const qtyInput = document.getElementById('spy-count');
  qtyInput.addEventListener('input', updateSuccessRate);

  document.getElementById('launch-form').addEventListener('submit', launchMission);
});

async function loadSpyInfo() {
  try {
    const res = await fetch('/api/kingdom/spies', {
      headers: { 'X-User-ID': currentUserId }
    });
    const data = await res.json();
    spyInfo = data;
    const qtyEl = document.getElementById('spy-count');
    qtyEl.max = data.spy_count || 1;
    qtyEl.value = 1;
    updateSuccessRate();
  } catch (err) {
    console.error('Failed to load spy info', err);
  }
}

async function loadKingdomSuggestions(query) {
  const list = document.getElementById('kingdom-list');
  if (!query) return (list.innerHTML = '');
  const { data, error } = await supabase
    .from('kingdoms')
    .select('kingdom_id, kingdom_name')
    .ilike('kingdom_name', `${query}%`)
    .limit(5);
  if (error) {
    console.error('Suggestion error:', error);
    return;
  }
  list.innerHTML = '';
  (data || []).forEach(k => {
    const opt = document.createElement('option');
    opt.value = k.kingdom_name;
    opt.dataset.id = k.kingdom_id;
    list.appendChild(opt);
  });
}

function updateSuccessRate() {
  const qty = parseInt(document.getElementById('spy-count').value, 10) || 0;
  const level = spyInfo.spy_level || 0;
  const rate = Math.min(95, 30 + level * 5 + qty * 10);
  const rateEl = document.getElementById('success-rate');
  rateEl.textContent = `Estimated Success Rate: ${rate}%`;
}

async function launchMission(e) {
  e.preventDefault();
  const name = document.getElementById('target-kingdom').value.trim();
  const list = document.getElementById('kingdom-list');
  const opt = Array.from(list.options).find(o => o.value === name);
  const target_id = opt ? opt.dataset.id : null;
  const mission_type = document.getElementById('mission-type').value;
  const count = parseInt(document.getElementById('spy-count').value, 10) || 1;
  if (!target_id) {
    showResult('Target kingdom not found.');
    return;
  }
  try {
    const res = await fetch('/api/spy/launch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': currentUserId
      },
      body: JSON.stringify({
        target_kingdom_name: name,
        mission_type,
        num_spies: count
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Launch failed');
    const msg = `Success: ${data.success ? 'Yes' : 'No'} | Accuracy: ${data.accuracy || '?'}% | Caught: ${data.caught ? 'Yes' : 'No'} | Spies Lost: ${data.spies_lost ?? '?'}`;
    showResult(msg);
  } catch (err) {
    showResult('Error: ' + err.message);
  }
}

function showResult(text) {
  const el = document.getElementById('mission-results');
  el.textContent = text;
}
