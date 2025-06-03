// seasonal_effects.js — FINAL AAA/SSS VERSION — 6.2.25
// Seasonal Effects Nexus Page Controller — FINAL architecture

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  // ✅ Initial load
  await loadSeasonalEffects();
});

// ✅ Load Seasonal Effects Nexus
async function loadSeasonalEffects() {
  const modifiersEl = document.getElementById('active-modifiers');
  const timerEl = document.getElementById('season-timer');
  const wheelEl = document.getElementById('forecast-wheel');
  const loreEl = document.getElementById('lore-scroll');
  const impactEl = document.getElementById('kingdom-impact');
  const marketEl = document.getElementById('market-projections');

  // Placeholders
  modifiersEl.innerHTML = "<p>Loading active modifiers...</p>";
  timerEl.innerHTML = "<p>Loading season timer...</p>";
  wheelEl.innerHTML = "<p>Loading forecast wheel...</p>";
  loreEl.innerHTML = "<p>Loading lore scroll...</p>";
  impactEl.innerHTML = "<p>Loading kingdom impact...</p>";
  marketEl.innerHTML = "<p>Loading market projections...</p>";

  try {
    // ✅ Load current season
    const { data: seasonData, error: seasonError } = await supabase
      .from('seasonal_effects')
      .select('*')
      .eq('active', true)
      .single();

    if (seasonError) throw seasonError;

    // ✅ Load upcoming seasons
    const { data: forecastData, error: forecastError } = await supabase
      .from('seasonal_effects')
      .select('*')
      .order('start_date', { ascending: true })
      .limit(4);

    if (forecastError) throw forecastError;

    // ✅ Render sections
    renderActiveModifiers(seasonData);
    renderSeasonTimer(seasonData.ends_at);
    renderForecastWheel(forecastData, seasonData.season_code);
    renderLoreScroll(seasonData);
    renderKingdomImpact(seasonData);
    renderMarketProjections(seasonData);

    // ✅ Start countdown timer
    startSeasonCountdown(seasonData.ends_at);

  } catch (err) {
    console.error("❌ Error loading Seasonal Effects Nexus:", err);
    showToast("Failed to load Seasonal Effects Nexus.");
  }
}

// ✅ Render Active Modifiers
function renderActiveModifiers(season) {
  const modifiersEl = document.getElementById('active-modifiers');
  modifiersEl.innerHTML = "";

  const modifiers = [
    { name: "Agriculture", effect: season.agriculture_modifier },
    { name: "Military", effect: season.military_modifier },
    { name: "Trade", effect: season.trade_modifier },
    { name: "Morale", effect: season.morale_modifier },
    { name: "Research", effect: season.research_modifier }
  ];

  modifiers.forEach(mod => {
    const card = document.createElement("div");
    card.classList.add("modifier-card");

    card.innerHTML = `
      <h4>${escapeHTML(mod.name)}</h4>
      <p>Effect: ${mod.effect >= 0 ? "+" : ""}${mod.effect}%</p>
    `;

    modifiersEl.appendChild(card);
  });
}

// ✅ Render Season Timer
function renderSeasonTimer(endsAt) {
  const timerEl = document.getElementById('season-timer');
  timerEl.innerHTML = `
    <h3>Time Remaining</h3>
    <p><span id="season-countdown">${formatTime(Math.max(0, Math.floor((new Date(endsAt).getTime() - Date.now()) / 1000)))}</span></p>
  `;
}

// ✅ Render Forecast Wheel
function renderForecastWheel(forecast, currentSeasonCode) {
  const wheelEl = document.getElementById('forecast-wheel');
  wheelEl.innerHTML = "";

  forecast.forEach(season => {
    const card = document.createElement("div");
    card.classList.add("forecast-card");
    if (season.season_code === currentSeasonCode) {
      card.classList.add("current-season");
    }

    card.innerHTML = `
      <h4>${escapeHTML(season.name)}</h4>
      <p>Starts: ${new Date(season.start_date).toLocaleDateString()}</p>
    `;

    wheelEl.appendChild(card);
  });
}

// ✅ Render Lore Scroll
function renderLoreScroll(season) {
  const loreEl = document.getElementById('lore-scroll');
  loreEl.innerHTML = `
    <h3>${escapeHTML(season.name)} Lore</h3>
    <p>${escapeHTML(season.lore_text || "No lore available.")}</p>
  `;
}

// ✅ Render Kingdom Impact
function renderKingdomImpact(season) {
  const impactEl = document.getElementById('kingdom-impact');
  impactEl.innerHTML = `
    <h3>Kingdom Impact</h3>
    <ul>
      <li>Food Production: ${season.agriculture_modifier >= 0 ? "+" : ""}${season.agriculture_modifier}%</li>
      <li>Military Strength: ${season.military_modifier >= 0 ? "+" : ""}${season.military_modifier}%</li>
      <li>Trade Revenue: ${season.trade_modifier >= 0 ? "+" : ""}${season.trade_modifier}%</li>
      <li>Kingdom Morale: ${season.morale_modifier >= 0 ? "+" : ""}${season.morale_modifier}%</li>
      <li>Research Speed: ${season.research_modifier >= 0 ? "+" : ""}${season.research_modifier}%</li>
    </ul>
  `;
}

// ✅ Render Market Projections
function renderMarketProjections(season) {
  const marketEl = document.getElementById('market-projections');
  marketEl.innerHTML = `
    <h3>Market Projections</h3>
    <p>${escapeHTML(season.market_projections || "No market projections available.")}</p>
  `;
}

// ✅ Start Countdown Timer
function startSeasonCountdown(endsAt) {
  const countdownEl = document.getElementById('season-countdown');

  const update = () => {
    const remaining = Math.max(0, Math.floor((new Date(endsAt).getTime() - Date.now()) / 1000));
    countdownEl.textContent = formatTime(remaining);

    if (remaining > 0) {
      requestAnimationFrame(update);
    } else {
      countdownEl.textContent = "Season Ended!";
    }
  };

  update();
}

// ✅ Helper: Format Time
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;

  return `${h}h ${m}m ${s}s`;
}

// ✅ Helper: Toast
function showToast(msg) {
  const toastEl = document.getElementById('toast');
  toastEl.textContent = msg;
  toastEl.classList.add("show");

  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
}

// ✅ Helper: Escape HTML
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
