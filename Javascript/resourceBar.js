// Project Name: Thronestead©
// File Name: resourceBar.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { fetchJson } from './utils.js'; // Custom wrapper for JSON fetch

// Dynamically load Bootstrap 5.3 if not already loaded
function injectBootstrap(onReady) {
  if (!document.querySelector('link[data-bootstrap]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css';
    link.setAttribute('data-bootstrap', 'true');
    document.head.appendChild(link);
  }

  const existing = document.querySelector('script[data-bootstrap]');
  if (!existing) {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js';
    script.defer = true;
    script.setAttribute('data-bootstrap', 'true');
    if (onReady) script.addEventListener('load', onReady, { once: true });
    document.head.appendChild(script);
  } else if (onReady) {
    if (window.bootstrap) {
      onReady();
    } else {
      existing.addEventListener('load', onReady, { once: true });
    }
  }
}

// List of resource keys and their emoji icons
const RESOURCES = [
  { key: 'gold', icon: '💰' }, { key: 'gems', icon: '💎' }, { key: 'wood', icon: '🌲' },
  { key: 'stone', icon: '🪨' }, { key: 'iron_ore', icon: '⛏' }, { key: 'food', icon: '🍞' },
  { key: 'coal', icon: '🔥' }, { key: 'livestock', icon: '🐄' }, { key: 'clay', icon: '🧱' },
  { key: 'flax', icon: '🌾' }, { key: 'tools', icon: '🛠' }, { key: 'wood_planks', icon: '🪵' },
  { key: 'refined_stone', icon: '🧱' }, { key: 'iron_ingots', icon: '🔩' }, { key: 'charcoal', icon: '🔥' },
  { key: 'leather', icon: '👞' }, { key: 'arrows', icon: '🏹' }, { key: 'swords', icon: '🗡' },
  { key: 'axes', icon: '🪓' }, { key: 'shields', icon: '🛡' }, { key: 'armor', icon: '🥋' },
  { key: 'wagon', icon: '🚚' }, { key: 'siege_weapons', icon: '🏰' }, { key: 'jewelry', icon: '💍' },
  { key: 'spear', icon: '🔱' }, { key: 'horses', icon: '🐎' }, { key: 'pitchforks', icon: '🍴' }
];

// Cache resource DOM elements for quick updates
const resourceEls = {};

// Create and inject the resource bar into the page
function createBar() {
  const bar = document.createElement('div');
  bar.id = 'resource-bar';
  bar.className = 'resource-bar d-flex flex-wrap justify-content-center gap-2 py-1 bg-dark text-white fs-sm';

  bar.innerHTML = RESOURCES.map(({ key, icon }) => `
    <a href="market.html?resource=${key}"
       class="text-white text-decoration-none"
       data-bs-toggle="tooltip"
       title="${key.replace(/_/g, ' ')}">
      <span class="resource-icon">${icon}</span>
      <span id="res-${key}">0</span>
    </a>`).join('');

  // Populate resourceEls map
  RESOURCES.forEach(({ key }) => {
    resourceEls[key] = bar.querySelector(`#res-${key}`);
  });

  const banner = document.querySelector('header.kr-top-banner');
  if (banner && banner.parentNode) {
    banner.insertAdjacentElement('afterend', bar);
  } else {
    document.body.prepend(bar);
  }

  // Initialize tooltips after Bootstrap loads
  initTooltips();
}

function initTooltips() {
  if (!window.bootstrap) return;
  const bar = document.getElementById('resource-bar');
  if (!bar) return;
  const tooltips = bar.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltips.forEach(el => new window.bootstrap.Tooltip(el));
}

// Fetch and update live resource values from server
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
    console.error('❌ Failed to fetch resource data:', err);
  }
}

// Populate each resource value into the bar
function updateUI(data) {
  RESOURCES.forEach(({ key }) => {
    const el = resourceEls[key];
    if (el && data[key] !== undefined) {
      el.textContent = data[key];
    }
  });
}

// Initialize everything once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  createBar();
  injectBootstrap(initTooltips);
  loadResources();
  setInterval(loadResources, 60000); // Auto-refresh every 60s
});
