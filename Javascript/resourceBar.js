import { supabase } from './supabaseClient.js';

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
    const res = await fetch('/api/resources', { headers });
    if (!res.ok) return;
    const { resources } = await res.json();
    updateUI(resources);
  } catch (err) {
    console.error('Failed to load resources', err);
  }
}

function updateUI(data) {
  const keys = ['gold','gems','wood','stone','iron_ore','food'];
  keys.forEach(k => {
    const el = document.getElementById(`res-${k}`);
    if (el && data[k] !== undefined) {
      el.textContent = data[k];
    }
  });
}

function createBar() {
  const bar = document.createElement('div');
  bar.id = 'resource-bar';
  bar.className = 'resource-bar';
  bar.innerHTML = `
    <a href="market.html?resource=gold" data-bs-toggle="tooltip" title="Gold">
      <span class="resource-icon">💰</span> <span id="res-gold">0</span>
    </a>
    <a href="market.html?resource=gems" data-bs-toggle="tooltip" title="Gems">
      <span class="resource-icon">💎</span> <span id="res-gems">0</span>
    </a>
    <a href="market.html?resource=wood" data-bs-toggle="tooltip" title="Wood">
      <span class="resource-icon">🌲</span> <span id="res-wood">0</span>
    </a>
    <a href="market.html?resource=stone" data-bs-toggle="tooltip" title="Stone">
      <span class="resource-icon">🪨</span> <span id="res-stone">0</span>
    </a>
    <a href="market.html?resource=iron_ore" data-bs-toggle="tooltip" title="Iron Ore">
      <span class="resource-icon">⛏</span> <span id="res-iron_ore">0</span>
    </a>
    <a href="market.html?resource=food" data-bs-toggle="tooltip" title="Food">
      <span class="resource-icon">🍞</span> <span id="res-food">0</span>
    </a>
  `;
  document.body.appendChild(bar);
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
