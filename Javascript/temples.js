// Project Name: Thronestead©
// File Name: temples.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML, showToast } from './utils.js';

let currentSession = null;
let currentKingdomId = null;
let templeChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  currentSession = session;

  // Get kingdom ID
  const { data: userData } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', session.user.id)
    .single();

  currentKingdomId = userData?.kingdom_id;
  if (!currentKingdomId) {
    showToast("Kingdom not found.");
    return;
  }

  subscribeToTempleUpdates(currentKingdomId);
  await loadTemplesNexus();
});

window.addEventListener('beforeunload', () => {
  if (templeChannel) supabase.removeChannel(templeChannel);
});

// ✅ Main Loader
async function loadTemplesNexus() {
  const overviewEl = document.getElementById('temple-overview-content');
  const favorBarEl = document.querySelector('.favor-bar-fill');
  const constructionEl = document.getElementById('temple-construction-options');
  const templeListEl = document.getElementById('temple-list-content');

  // Loading placeholders
  overviewEl.innerHTML = "<p>Loading temple overview...</p>";
  favorBarEl.style.width = '0%';
  constructionEl.innerHTML = "<p>Loading construction options...</p>";
  templeListEl.innerHTML = "<p>Loading your temples...</p>";

  try {
    const kingdomId = currentKingdomId;

    // 🔹 Fetch temples
    const { data: templesData, error: templesError } = await supabase
      .from('kingdom_temples')
      .select('*')
      .eq('kingdom_id', kingdomId);

    if (templesError) throw templesError;

    // 🔹 Fetch divine favor
    const { data: favorData, error: favorError } = await supabase
      .from('kingdoms')
      .select('divine_favor')
      .eq('kingdom_id', kingdomId)
      .single();

    if (favorError) throw favorError;

    const majorTemple = templesData.find(t => t.is_major);
    const subTemples = templesData.filter(t => !t.is_major);

    renderTempleOverview(majorTemple);
    renderFavorBar(favorData.divine_favor);
    renderConstructionOptions();
    renderTempleList(subTemples);

  } catch (err) {
    console.error("❌ Temple Load Error:", err);
    showToast("Failed to load Temples Nexus.");
  }
}

// ✅ Render Major Temple
function renderTempleOverview(temple) {
  const el = document.getElementById('temple-overview-content');
  el.innerHTML = "";

  if (!temple) {
    el.innerHTML = "<p>No major temple constructed yet.</p>";
    return;
  }

  const div = document.createElement("div");
  div.className = "temple-card";
  div.innerHTML = `
    <h3>${escapeHTML(temple.temple_name)}</h3>
    <p>Level: ${temple.level}</p>
    <p>Type: ${escapeHTML(temple.temple_type)}</p>
  `;
  el.appendChild(div);
}

// ✅ Render Divine Favor Bar
function renderFavorBar(favor) {
  const el = document.querySelector('.favor-bar-fill');
  const safeVal = Math.min(Math.max(favor, 0), 100);
  el.style.width = `${safeVal}%`;
  el.textContent = `${safeVal}%`;
}

// ✅ Render Construction Options
function renderConstructionOptions() {
  const el = document.getElementById('temple-construction-options');
  el.innerHTML = "";

  const types = [
    "Temple of Light",
    "Temple of War",
    "Temple of Wisdom",
    "Temple of Nature"
  ];

  types.forEach(type => {
    const btn = document.createElement("button");
    btn.className = "action-btn";
    btn.textContent = `Construct ${type}`;
    btn.addEventListener("click", () => constructTemple(type));
    el.appendChild(btn);
  });
}

// ✅ Render Sub-Temples
function renderTempleList(subTemples) {
  const el = document.getElementById('temple-list-content');
  el.innerHTML = "";

  if (subTemples.length === 0) {
    el.innerHTML = "<p>No sub-temples constructed yet.</p>";
    return;
  }

  subTemples.forEach(t => {
    const card = document.createElement("div");
    card.className = "temple-card";
    card.innerHTML = `
      <h4>${escapeHTML(t.temple_name)}</h4>
      <p>Level: ${t.level}</p>
      <p>Type: ${escapeHTML(t.temple_type)}</p>
    `;
    el.appendChild(card);
  });
}

// ✅ Realtime Updates
function subscribeToTempleUpdates(kid) {
  templeChannel = supabase
    .channel(`temples-${kid}`)
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'kingdom_temples',
      filter: `kingdom_id=eq.${kid}`
    }, async () => {
      await loadTemplesNexus();
    })
    .subscribe();
}

// ✅ Construct Temple Handler
async function constructTemple(type) {
  if (!confirm(`Construct a new "${type}"?`)) return;

  try {
    const res = await fetch("/api/kingdom/construct_temple", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'Authorization': `Bearer ${currentSession.access_token}`,
        'X-User-ID': currentSession.user.id
      },
      body: JSON.stringify({ temple_type: type })
    });

    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to construct temple");

    showToast(`Temple "${type}" constructed!`);
    await loadTemplesNexus();

  } catch (err) {
    console.error("❌ Construct Temple Error:", err);
    showToast("Failed to construct temple.");
  }
}

