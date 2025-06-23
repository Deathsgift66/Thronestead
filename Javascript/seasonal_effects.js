// Project Name: Thronestead©
// File Name: seasonal_effects.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  await loadSeasonalEffects(session);
});

// ✅ Load Seasonal Effects Nexus
async function loadSeasonalEffects(session) {
  const ui = {
    modifiers: document.getElementById('active-modifiers'),
    timer: document.getElementById('season-timer'),
    wheel: document.getElementById('forecast-wheel'),
    lore: document.getElementById('lore-scroll'),
    impact: document.getElementById('kingdom-impact'),
    market: document.getElementById('market-projections')
  };

  // Set placeholders
  Object.entries(ui).forEach(([_, el]) => {
    el.innerHTML = `<p>Loading...</p>`;
  });

  try {
    const res = await fetch('/api/seasonal-effects', {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'X-User-ID': session.user.id
      }
    });

    const { current, forecast } = await res.json();

    renderActiveModifiers(current);
    renderSeasonTimer(current.ends_at);
    renderForecastWheel(forecast, current.season_code);
    renderLoreScroll(current);
    renderKingdomImpact(current);
    renderMarketProjections(current);
    startSeasonCountdown(current.ends_at);

  } catch (err) {
    console.error("❌ Error loading Seasonal Effects Nexus:", err);
    showToast("Failed to load Seasonal Effects Nexus.");
  }
}

// ✅ Render Active Modifiers
function renderActiveModifiers(season) {
  const container = document.getElementById('active-modifiers');
  container.innerHTML = '';

  const fields = [
    ["Agriculture", season.agriculture_modifier],
    ["Military", season.military_modifier],
    ["Trade", season.trade_modifier],
    ["Morale", season.morale_modifier],
    ["Research", season.research_modifier]
  ];

  fields.forEach(([label, value]) => {
    const card = document.createElement('div');
    card.className = 'modifier-card';
    card.innerHTML = `
      <h4>${escapeHTML(label)}</h4>
      <p>Effect: ${value >= 0 ? '+' : ''}${value}%</p>
    `;
    container.appendChild(card);
  });
}

// ✅ Render Countdown Timer Section
function renderSeasonTimer(endsAt) {
  const el = document.getElementById('season-timer');
  const secondsLeft = Math.max(0, Math.floor((new Date(endsAt).getTime() - Date.now()) / 1000));

  el.innerHTML = `
    <h3>Time Remaining</h3>
    <p><span id="season-countdown">${formatTime(secondsLeft)}</span></p>
  `;
}

// ✅ Render Forecast Wheel (Clickable Cards)
function renderForecastWheel(forecast, currentCode) {
  const container = document.getElementById('forecast-wheel');
  container.innerHTML = '';

  forecast.forEach(season => {
    const card = document.createElement('div');
    card.className = 'forecast-card';
    if (season.season_code === currentCode) {
      card.classList.add('current-season');
    }
    card.innerHTML = `
      <h4>${escapeHTML(season.name)}</h4>
      <p>Starts: ${new Date(season.start_date).toLocaleDateString()}</p>
    `;
    card.addEventListener('click', () => openForecastModal(season));
    container.appendChild(card);
  });
}

// ✅ Render Lore Scroll Section
function renderLoreScroll(season) {
  const el = document.getElementById('lore-scroll');
  el.innerHTML = `
    <h3>${escapeHTML(season.name)} Lore</h3>
    <p>${escapeHTML(season.lore_text || 'No lore available.')}</p>
  `;
}

// ✅ Render Kingdom-Specific Effects Summary
function renderKingdomImpact(season) {
  const el = document.getElementById('kingdom-impact');
  el.innerHTML = `
    <h3>Kingdom Impact</h3>
    <ul>
      <li>Food Production: ${fmtSigned(season.agriculture_modifier)}%</li>
      <li>Military Strength: ${fmtSigned(season.military_modifier)}%</li>
      <li>Trade Revenue: ${fmtSigned(season.trade_modifier)}%</li>
      <li>Kingdom Morale: ${fmtSigned(season.morale_modifier)}%</li>
      <li>Research Speed: ${fmtSigned(season.research_modifier)}%</li>
    </ul>
  `;
}

// ✅ Render Market Predictions
function renderMarketProjections(season) {
  const el = document.getElementById('market-projections');
  el.innerHTML = `
    <h3>Market Projections</h3>
    <p>${escapeHTML(season.market_projections || 'No market projections available.')}</p>
  `;
}

// ✅ Animate Countdown
function startSeasonCountdown(endsAt) {
  const countdownEl = document.getElementById('season-countdown');
  if (!countdownEl) return;

  const update = () => {
    const remaining = Math.max(0, Math.floor((new Date(endsAt).getTime() - Date.now()) / 1000));
    countdownEl.textContent = formatTime(remaining);
    if (remaining > 0) requestAnimationFrame(update);
    else countdownEl.textContent = "Season Ended!";
  };

  update();
}

// ✅ Modal for Forecast Preview
function openForecastModal(season) {
  const overlay = document.getElementById('forecast-modal');
  const body = document.getElementById('forecast-modal-body');

  body.innerHTML = `
    <h3>${escapeHTML(season.name)}</h3>
    <p>${escapeHTML(season.lore_text || 'No details')}</p>
  `;

  overlay.classList.remove('hidden');
  document.getElementById('close-forecast-modal').onclick = () => {
    overlay.classList.add('hidden');
  };
}

// ✅ Time Formatting (h m s)
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

// ✅ Sign Formatter
function fmtSigned(val) {
  return (val >= 0 ? '+' : '') + val;
}

// ✅ Toast Display
function showToast(msg) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// ✅ Escape HTML to prevent injection
