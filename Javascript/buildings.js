// buildings.js — FINAL AAA/SSS VERSION — 6.2.25
// Hardened Buildings Management Page

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "login.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load
  await loadBuildings();
});

// ✅ Load Buildings
async function loadBuildings() {
  const tbody = document.getElementById("buildingsTableBody");

  tbody.innerHTML = `
    <tr><td colspan="5">Loading buildings...</td></tr>
  `;

  try {
    // ✅ Get user
    const { data: { user } } = await supabase.auth.getUser();

    // ✅ Get user's kingdom ID
    const { data: kingdomData, error: kingdomError } = await supabase
      .from('players')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    if (kingdomError || !kingdomData?.kingdom_id) {
      throw new Error("Failed to load kingdom ID.");
    }

    const kingdomId = kingdomData.kingdom_id;

    // ✅ Get kingdom buildings
    const { data: buildingsData, error: buildingsError } = await supabase
      .from('kingdom_buildings')
      .select('*')
      .eq('kingdom_id', kingdomId);

    if (buildingsError) {
      throw new Error("Failed to load kingdom buildings.");
    }

    if (!buildingsData || buildingsData.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="5">No buildings constructed.</td></tr>
      `;
      return;
    }

    // ✅ Preload building catalogue
    const { data: catalogueData, error: catalogueError } = await supabase
      .from('building_catalogue')
      .select('*');

    if (catalogueError) {
      throw new Error("Failed to load building catalogue.");
    }

    // ✅ Build lookup map
    const catalogueMap = {};
    catalogueData.forEach(b => {
      catalogueMap[b.building_id] = b;
    });

    // ✅ Populate table
    tbody.innerHTML = "";

    buildingsData.forEach(building => {
      const catalog = catalogueMap[building.building_id];

      if (!catalog) return; // Skip unknown building

      const production = catalog.production_rate ? `${catalog.production_rate * building.level} ${catalog.production_type}` : "N/A";
      const upkeep = catalog.upkeep ? `${catalog.upkeep * building.level}` : "None";

      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${escapeHTML(catalog.building_name)}</td>
        <td>${building.level}</td>
        <td>${production}</td>
        <td>${upkeep}</td>
        <td>
          <button class="action-btn upgrade-btn" data-building-id="${building.building_id}">Upgrade</button>
        </td>
      `;

      tbody.appendChild(row);
    });

    // ✅ Bind Upgrade buttons
    document.querySelectorAll(".upgrade-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const buildingId = btn.dataset["buildingId"];

        try {
          const res = await fetch("/api/buildings/upgrade", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ building_id: buildingId })
          });
          const result = await res.json();
          alert(result.message || "Building upgraded.");
          await loadBuildings();
        } catch (err) {
          console.error("❌ Error upgrading building:", err);
          alert("Upgrade failed.");
        }
      });
    });

  } catch (err) {
    console.error("❌ Error loading buildings:", err);
    tbody.innerHTML = `
      <tr><td colspan="5">Failed to load buildings.</td></tr>
    `;
  }
}

// ✅ Basic HTML escape
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
