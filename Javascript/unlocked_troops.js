// Project Name: Thronestead©
// File Name: unlocked_troops.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './core_utils.js';

let userId = null;
let kingdomId = null;
let realtimeChannel = null;

function setupToggleButtons() {
  document.querySelectorAll('.toggle-btn').forEach(btn => {
    const target = document.getElementById(btn.dataset.target);
    if (!target) return;
    btn.addEventListener('click', () => {
      const expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!expanded));
      btn.textContent = `${btn.dataset.label} ${expanded ? '▲' : '▼'}`;
      target.classList.toggle('hidden', expanded);
    });
  });
}

document.addEventListener('DOMContentLoaded', init);

async function init() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  userId = session.user.id;
  const { data } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', userId)
    .single();
  kingdomId = data?.kingdom_id;

  setupToggleButtons();
  await loadUnits();
  subscribeRealtime();
}

async function loadUnits() {
  try {
    const res = await fetch('/api/kingdom_troops/unlocked', {
      headers: { 'X-User-ID': userId }
    });
    if (!res.ok) throw new Error('Failed to load units');
    const { unlockedUnits, unitStats } = await res.json();
    renderUnits(unlockedUnits, unitStats);
    const loading = document.getElementById('units-loading');
    if (loading) loading.remove();
  } catch (err) {
    console.error('loadUnits error:', err);
    const loading = document.getElementById('units-loading');
    if (loading) loading.textContent = 'Failed to load units.';
  }
}

function renderUnits(unlocked, stats) {
  const categories = {
    Infantry: [],
    Archers: [],
    Cavalry: [],
    Siege: [],
    Support: []
  };

  unlocked.forEach(t => {
    const s = stats[t];
    if (!s || !categories[s.class]) return;
    categories[s.class].push(s);
    const img = new Image();
    img.src = `/assets/troops/${t}.png`;
  });

  for (const cls in categories) {
    const listEl = document.getElementById(`${cls.toLowerCase()}-list`);
    if (!listEl) continue;
    listEl.innerHTML = '';
    const frag = document.createDocumentFragment();
    const items = categories[cls].sort((a, b) => a.tier - b.tier);
    if (!items.length) {
      listEl.innerHTML = '<p>No units unlocked.</p>';
    } else {
      items.forEach(u => frag.appendChild(createCard(u)));
      listEl.appendChild(frag);
    }
  }
}

function createCard(unit) {
  const card = document.createElement('div');
  card.className = 'unit-card';
  card.innerHTML = `
    <img src="/assets/troops/${unit.unit_type}.png" alt="${escapeHTML(unit.name)}" onerror="this.src='/Assets/icon-sword.svg'; this.onerror=null;">
    <h3>${escapeHTML(unit.name)}</h3>
    <p>Tier ${unit.tier}</p>
    <ul class="unit-stats">
      <li>Dmg: ${unit.damage}</li>
      <li>Def: ${unit.defense}</li>
      <li>HP: ${unit.hp}</li>
      <li>Speed: ${unit.speed}</li>
      <li>Range: ${unit.range}</li>
    </ul>`;
  return card;
}

function subscribeRealtime() {
  if (!kingdomId) return;
  realtimeChannel = supabase
    .channel('troops-' + kingdomId)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'kingdom_troops',
      filter: `kingdom_id=eq.${kingdomId}`
    }, loadUnits)
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}
