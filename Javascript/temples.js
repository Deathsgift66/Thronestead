/*
Project Name: Kingmakers Rise Frontend
File Name: temples.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  // ✅ Initial load
  await loadTemplesNexus();
});

// ✅ Load Temples Nexus
async function loadTemplesNexus() {
  const overviewEl = document.getElementById('temple-overview-content');
  const favorBarEl = document.querySelector('.favor-bar-fill');
  const constructionEl = document.getElementById('temple-construction-options');
  const templeListEl = document.getElementById('temple-list-content');

  // Placeholders
  overviewEl.innerHTML = "<p>Loading temple overview...</p>";
  favorBarEl.style.width = '0%';
  constructionEl.innerHTML = "<p>Loading construction options...</p>";
  templeListEl.innerHTML = "<p>Loading your temples...</p>";

  try {
    // ✅ Load user
    const { data: { user } } = await supabase.auth.getUser();

    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const kingdomId = userData.kingdom_id;

    // ✅ Load kingdom temples
    const { data: templesData, error: templesError } = await supabase
      .from('temples')
      .select('*')
      .eq('kingdom_id', kingdomId);

    if (templesError) throw templesError;

    // ✅ Load divine favor (assumed field)
    const { data: favorData, error: favorError } = await supabase
      .from('kingdoms')
      .select('divine_favor')
      .eq('kingdom_id', kingdomId)
      .single();

    if (favorError) throw favorError;

    // ✅ Split major / sub temples
    const majorTemple = templesData.find(t => t.is_major);
    const subTemples = templesData.filter(t => !t.is_major);

    // ✅ Render major temple overview
    renderTempleOverview(majorTemple);

    // ✅ Render favor bar
    renderFavorBar(favorData.divine_favor);

    // ✅ Render construction options
    renderConstructionOptions();

    // ✅ Render your temples list
    renderTempleList(subTemples);

  } catch (err) {
    console.error("❌ Error loading Temples Nexus:", err);
    showToast("Failed to load Temples Nexus.");
  }
}

// ✅ Render Temple Overview
function renderTempleOverview(temple) {
  const overviewEl = document.getElementById('temple-overview-content');
  overviewEl.innerHTML = "";

  if (!temple) {
    overviewEl.innerHTML = "<p>No major temple constructed yet.</p>";
    return;
  }

  const card = document.createElement("div");
  card.classList.add("temple-card");

  card.innerHTML = `
    <h3>${escapeHTML(temple.temple_name)}</h3>
    <p>Level: ${temple.level}</p>
    <p>Type: ${escapeHTML(temple.temple_type)}</p>
  `;

  overviewEl.appendChild(card);
}

// ✅ Render Favor Bar
function renderFavorBar(favorValue) {
  const favorBarEl = document.querySelector('.favor-bar-fill');
  const clampedFavor = Math.min(Math.max(favorValue, 0), 100);
  favorBarEl.style.width = `${clampedFavor}%`;
  favorBarEl.textContent = `${clampedFavor}%`;
}

// ✅ Render Construction Options
function renderConstructionOptions() {
  const constructionEl = document.getElementById('temple-construction-options');
  constructionEl.innerHTML = "";

  const templeTypes = ["Temple of Light", "Temple of War", "Temple of Wisdom", "Temple of Nature"];

  templeTypes.forEach(type => {
    const btn = document.createElement("button");
    btn.classList.add("action-btn");
    btn.textContent = `Construct ${type}`;
    btn.addEventListener("click", () => constructTemple(type));
    constructionEl.appendChild(btn);
  });
}

// ✅ Render Your Temples List
function renderTempleList(subTemples) {
  const templeListEl = document.getElementById('temple-list-content');
  templeListEl.innerHTML = "";

  if (subTemples.length === 0) {
    templeListEl.innerHTML = "<p>No sub-temples constructed yet.</p>";
    return;
  }

  subTemples.forEach(temple => {
    const card = document.createElement("div");
    card.classList.add("temple-card");

    card.innerHTML = `
      <h4>${escapeHTML(temple.temple_name)}</h4>
      <p>Level: ${temple.level}</p>
      <p>Type: ${escapeHTML(temple.temple_type)}</p>
    `;

    templeListEl.appendChild(card);
  });
}

// ✅ Construct Temple Action
async function constructTemple(templeType) {
  if (!confirm(`Construct a new "${templeType}"?`)) return;

  try {
    const res = await fetch("/api/kingdom/construct_temple", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ temple_type: templeType })
    });

    const result = await res.json();

    if (!res.ok) throw new Error(result.error || "Failed to construct temple.");

    showToast(`Temple "${templeType}" constructed!`);
    await loadTemplesNexus();

  } catch (err) {
    console.error("❌ Error constructing temple:", err);
    showToast("Failed to construct temple.");
  }
}

// ✅ Helper: Toast
function showToast(msg) {
  let toastEl = document.getElementById('toast');

  // Inject toast if not present
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.id = "toast";
    toastEl.className = "toast-notification";
    document.body.appendChild(toastEl);
  }

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
