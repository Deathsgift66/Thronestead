/*
Project Name: Kingmakers Rise Frontend
File Name: treaty_web.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Treaty Web Nexus Page Controller

import { supabase } from './supabaseClient.js';
import { DataSet, Network } from 'https://cdn.jsdelivr.net/npm/vis-network/standalone/esm/vis-network.min.js';


let network = null;
let allTreaties = [];

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  initControls();
  await loadTreatyWeb();
});

// ✅ Initialize Control Buttons
function initControls() {
  document.getElementById('refreshGraph').addEventListener('click', async () => {
    showToast("Refreshing Treaty Web...");
    await loadTreatyWeb();
  });

  document.getElementById('toggleLegend').addEventListener('click', () => {
    let legend = document.getElementById('legend-panel');
    if (!legend) {
      // Inject legend panel if not present
      legend = document.createElement('div');
      legend.id = 'legend-panel';
      legend.className = 'legend-panel';
      legend.innerHTML = `
        <h4>Treaty Web Legend</h4>
        <ul>
          <li><span style="color: green;">Alliance → Alliance Treaty</span></li>
          <li><span style="color: blue;">Alliance → Kingdom Treaty</span></li>
          <li><span style="color: orange;">Kingdom → Kingdom Treaty</span></li>
        </ul>
      `;
      document.body.appendChild(legend);
    }
    legend.classList.toggle('hidden');
  });

  document.getElementById('timelineRange').addEventListener('input', () => {
    filterTreatyWeb();
  });
}

// ✅ Load Treaty Web Data and Render Graph
async function loadTreatyWeb() {
  try {
    // ✅ Load alliances
    const { data: alliances, error: alliancesError } = await supabase
      .from('alliances')
      .select('alliance_id, name');

    if (alliancesError) throw alliancesError;

    // ✅ Load kingdoms
    const { data: kingdoms, error: kingdomsError } = await supabase
      .from('users')
      .select('kingdom_id, kingdom_name');

    if (kingdomsError) throw kingdomsError;

    // ✅ Load treaties
    const { data: treaties, error: treatiesError } = await supabase
      .from('alliance_treaties')
      .select('*');

    if (treatiesError) throw treatiesError;

    // ✅ Store all treaties for timeline filtering
    allTreaties = treaties;

    // ✅ Build Graph
    const nodes = new DataSet();
    const edges = new DataSet();

    // Add Alliance nodes
    alliances.forEach(a => {
      nodes.add({
        id: `A-${a.alliance_id}`,
        label: a.name,
        shape: 'ellipse',
        color: 'green'
      });
    });

    // Add Kingdom nodes
    kingdoms.forEach(k => {
      nodes.add({
        id: `K-${k.kingdom_id}`,
        label: k.kingdom_name,
        shape: 'box',
        color: 'orange'
      });
    });

    // Add Treaty edges
    treaties.forEach(t => {
      let source = "";
      let target = "";
      let color = "";

      if (t.type === "Alliance → Alliance") {
        source = `A-${t.alliance_id_source}`;
        target = `A-${t.alliance_id_target}`;
        color = 'green';
      } else if (t.type === "Alliance → Kingdom") {
        source = `A-${t.alliance_id_source}`;
        target = `K-${t.kingdom_id_target}`;
        color = 'blue';
      } else if (t.type === "Kingdom → Kingdom") {
        source = `K-${t.kingdom_id_source}`;
        target = `K-${t.kingdom_id_target}`;
        color = 'orange';
      }

      edges.add({
        from: source,
        to: target,
        color: { color: color },
        label: t.treaty_type || "Treaty",
        arrows: "to"
      });
    });

    // ✅ Draw Graph
    const container = document.getElementById('network');
    const data = { nodes, edges };
    const options = {
      physics: {
        stabilization: false,
        barnesHut: {
          gravitationalConstant: -30000,
          springLength: 150
        }
      },
      edges: {
        smooth: true
      },
      nodes: {
        font: { size: 16 }
      }
    };

    network = new Network(container, data, options);

    showToast("Treaty Web loaded!");

  } catch (err) {
    console.error("❌ Error loading Treaty Web:", err);
    showToast("Failed to load Treaty Web.");
  }
}

// ✅ Filter Treaty Web by Timeline
function filterTreatyWeb() {
  if (!network || !allTreaties.length) return;

  const timelineVal = document.getElementById('timelineRange').value;
  const days = parseInt(timelineVal);

  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  const edges = network.body.data.edges;

  edges.forEach(edge => {
    const treaty = allTreaties.find(t => {
      let source = "";
      let target = "";

      if (t.type === "Alliance → Alliance") {
        source = `A-${t.alliance_id_source}`;
        target = `A-${t.alliance_id_target}`;
      } else if (t.type === "Alliance → Kingdom") {
        source = `A-${t.alliance_id_source}`;
        target = `K-${t.kingdom_id_target}`;
      } else if (t.type === "Kingdom → Kingdom") {
        source = `K-${t.kingdom_id_source}`;
        target = `K-${t.kingdom_id_target}`;
      }

      return edge.from === source && edge.to === target;
    });

    if (treaty) {
      const createdAt = new Date(treaty.created_at);
      if (createdAt >= cutoffDate) {
        edges.update({ id: edge.id, hidden: false });
      } else {
        edges.update({ id: edge.id, hidden: true });
      }
    }
  });
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
