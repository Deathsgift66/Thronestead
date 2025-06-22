// Project Name: Thronestead©
// File Name: unlocked_troops.js
// Version 6.14.2025
// Developer: Codex
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';

let userId = null;
let kingdomId = null;
let realtimeChannel = null;

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

  await loadUnits();
  subscribeRealtime();
}

async function loadUnits() {
  try {
    const res = await fetch('https://thronestead.onrender.com/api/kingdom_troops/unlocked', {
      headers: { 'X-User-ID': userId }
    });
    if (!res.ok) throw new Error('Failed to load units');
    const { unlockedUnits, unitStats } = await res.json();
    renderUnits(unlockedUnits, unitStats);
  } catch (err) {
    console.error('loadUnits error:', err);
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
    img.src = `/images/troops/${t}.png`;
  });

  for (const cls in categories) {
    const listEl = document.getElementById(`${cls.toLowerCase()}-list`);
    if (!listEl) continue;
    listEl.innerHTML = '';
    const frag = document.createDocumentFragment();
    categories[cls]
      .sort((a, b) => a.tier - b.tier)
      .forEach(u => frag.appendChild(createCard(u)));
    listEl.appendChild(frag);
  }
}

function createCard(unit) {
  const card = document.createElement('div');
  card.className = 'unit-card';
  card.innerHTML = `
    <img src="/images/troops/${unit.unit_type}.png" alt="${escapeHTML(unit.name)}" onerror="this.src='/Assets/icon-sword.svg'; this.onerror=null;">
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
