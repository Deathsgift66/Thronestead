import { supabase } from './supabaseClient.js';
import { fetchJson } from './fetchJson.js';

function injectBootstrap() {
  if (!document.querySelector('link[data-bootstrap]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css';
    link.setAttribute('data-bootstrap', 'true');
    document.head.appendChild(link);
  }
  if (!document.querySelector('script[data-bootstrap]')) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js';
    script.defer = true;
    script.setAttribute('data-bootstrap', 'true');
    document.head.appendChild(script);
  }
}

async function loadResources() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const uid = session?.user?.id;
    if (!uid) return;

    const token = session.access_token;
    const headers = { Authorization: `Bearer ${token}`, 'X-User-ID': uid };
    const payload = await fetchJson('/api/resources', { headers });

    updateUI(payload.resources || {});
  } catch (err) {
    console.error('Invalid JSON from /api/resources:', err);
  }
}

const RESOURCES = [
  { key: 'gold', icon: '💰' },
  { key: 'gems', icon: '💎' },
  { key: 'wood', icon: '🌲' },
  { key: 'stone', icon: '🪨' },
  { key: 'iron_ore', icon: '⛏' },
  { key: 'food', icon: '🍞' },
  { key: 'coal', icon: '🔥' },
  { key: 'livestock', icon: '🐄' },
  { key: 'clay', icon: '🧱' },
  { key: 'flax', icon: '🌾' },
  { key: 'tools', icon: '🛠' },
  { key: 'wood_planks', icon: '🪵' },
  { key: 'refined_stone', icon: '🧱' },
  { key: 'iron_ingots', icon: '🔩' },
  { key: 'charcoal', icon: '🔥' },
  { key: 'leather', icon: '👞' },
  { key: 'arrows', icon: '🏹' },
  { key: 'swords', icon: '🗡' },
  { key: 'axes', icon: '🪓' },
  { key: 'shields', icon: '🛡' },
  { key: 'armour', icon: '🥋' },
  { key: 'wagon', icon: '🚚' },
  { key: 'siege_weapons', icon: '🏰' },
  { key: 'jewelry', icon: '💍' },
  { key: 'spear', icon: '🔱' },
  { key: 'horses', icon: '🐎' },
  { key: 'pitchforks', icon: '🍴' }
];

function updateUI(data) {
  RESOURCES.forEach(({ key }) => {
    const el = document.getElementById(`res-${key}`);
    if (el && data[key] !== undefined) {
      el.textContent = data[key];
    }
  });
}

function createBar() {
  const bar = document.createElement('div');
  bar.id = 'resource-bar';
  bar.className = 'resource-bar';
  bar.innerHTML = RESOURCES.map(r =>
    `<a href="market.html?resource=${r.key}" data-bs-toggle="tooltip" title="${r.key.replace(/_/g,' ')}">` +
    `<span class="resource-icon">${r.icon}</span> <span id="res-${r.key}">0</span>` +
    `</a>`
  ).join(' ');

  const banner = document.querySelector('header.kr-top-banner');
  if (banner && banner.parentNode) {
    banner.insertAdjacentElement('afterend', bar);
  } else {
    document.body.prepend(bar);
  }
  if (window.bootstrap) {
    const triggers = bar.querySelectorAll('[data-bs-toggle="tooltip"]');
    triggers.forEach(el => new window.bootstrap.Tooltip(el));
  }
}

document.addEventListener('DOMContentLoaded', () => {
  injectBootstrap();
  createBar();
  loadResources();
});
