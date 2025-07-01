// Project Name: Thronestead©
// File Name: treaty_web.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7/+esm';

let rawData = { nodes: [], links: [] };
let svg, linkGroup, nodeGroup, simulation;
const typeColor = {
  MDP: 'blue',
  protection: 'green',
  NAP: 'gold',
  war: 'red'
};

document.addEventListener('DOMContentLoaded', async () => {
  initControls();
  await loadNetwork();
  window.addEventListener('resize', resizeGraph);
});

// ✅ Load Network Data from API
async function loadNetwork() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const headers = session ? { 'X-User-ID': session.user.id } : {};
    const res = await fetch('/api/treaty_web/data', { headers });
    const data = await res.json();

    rawData.nodes = (data.alliances || []).map(a => ({
      alliance_id: a.alliance_id,
      name: a.name,
      level: a.level,
      emblem_url: a.emblem_url,
    }));

    rawData.links = (data.treaties || []).map(t => ({
      treaty_id: t.treaty_id,
      source: t.alliance_id,
      target: t.partner_alliance_id,
      type: t.treaty_type,
      status: t.status,
      date_signed: t.signed_at,
    }));

    renderGraph();
    showToast('Treaty network loaded');
  } catch (err) {
    console.error('❌ Failed to load treaty network:', err);
    showToast('Failed to load network');
  }
}

// ✅ Initialize SVG + Force Layout
function renderGraph() {
  const container = document.getElementById('network');
  container.innerHTML = '';
  const width = container.clientWidth;
  const height = container.clientHeight;

  svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height);

  const zoomGroup = svg.append('g');
  svg.call(d3.zoom().on('zoom', e => zoomGroup.attr('transform', e.transform)));

  linkGroup = zoomGroup.append('g').attr('stroke-opacity', 0.7);
  nodeGroup = zoomGroup.append('g');

  simulation = d3.forceSimulation(rawData.nodes)
    .force('link', d3.forceLink(rawData.links).id(d => d.alliance_id).distance(120))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2));

  updateGraph();
}

// ✅ D3 Graph Update Function
function updateGraph() {
  const active = Array.from(document.querySelectorAll('.filter-btn.active'))
    .map(b => b.dataset.type);
  const filteredLinks = rawData.links.filter(l => active.includes(l.type));

  // Update Links
  const linkSel = linkGroup.selectAll('line')
    .data(filteredLinks, d => d.treaty_id);

  linkSel.exit().remove();

  const linkEnter = linkSel.enter().append('line')
    .attr('stroke-width', 2)
    .attr('stroke', d => typeColor[d.type] || '#999')
    .attr('class', d => d.type === 'war' && d.status === 'active' ? 'war-active' : null);

  linkEnter.append('title').text(d => `${d.type.toUpperCase()} – ${d.date_signed || 'Pending'}`);
  linkSel.merge(linkEnter);

  // Update Nodes
  const nodeSel = nodeGroup.selectAll('g')
    .data(rawData.nodes, d => d.alliance_id);

  nodeSel.exit().remove();

  const nodeEnter = nodeSel.enter().append('g')
    .attr('tabindex', 0)
    .on('click', (e, d) => {
      window.location.href = `alliance_home.html?aid=${d.alliance_id}`;
    });

  nodeEnter.append('circle')
    .attr('r', 22)
    .attr('fill', '#ccc');

  nodeEnter.append('image')
    .attr('href', d => d.emblem_url || '/Assets/avatars/default_avatar_emperor.png')
    .attr('width', 40)
    .attr('height', 40)
    .attr('x', -20)
    .attr('y', -20)
    .attr('clip-path', 'circle(20px at 20px 20px)');

  nodeEnter.append('title')
    .text(d => `${d.name} (Lv ${d.level})`);

  nodeSel.merge(nodeEnter);

  simulation.nodes(rawData.nodes).on('tick', ticked);
  simulation.force('link').links(filteredLinks);
  simulation.alpha(1).restart();
}

// ✅ Force Tick Layout
function ticked() {
  linkGroup.selectAll('line')
    .attr('x1', d => d.source.x)
    .attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x)
    .attr('y2', d => d.target.y);

  nodeGroup.selectAll('g')
    .attr('transform', d => `translate(${d.x},${d.y})`);
}

// ✅ Resize on Window
function resizeGraph() {
  if (!svg) return;
  const container = document.getElementById('network');
  const width = container.clientWidth;
  const height = container.clientHeight;
  svg.attr('width', width).attr('height', height);
  simulation.force('center', d3.forceCenter(width / 2, height / 2)).alpha(0.5).restart();
}

// ✅ Controls and Filters
function initControls() {
  document.getElementById('refreshGraph')?.addEventListener('click', loadNetwork);
  document.getElementById('toggleLegend')?.addEventListener('click', toggleLegend);

  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.classList.toggle('active');
      updateGraph();
    });
  });
}

// ✅ Toggle Legend Panel
function toggleLegend() {
  let legend = document.getElementById('legend-panel');
  if (!legend) {
    legend = document.createElement('div');
    legend.id = 'legend-panel';
    legend.className = 'legend-panel';
    legend.innerHTML = `
      <h4>Treaty Types</h4>
      <ul>
        <li><span data-color="blue">&#9679;</span> MDP</li>
        <li><span data-color="green">&#9679;</span> Protection</li>
        <li><span data-color="gold">&#9679;</span> NAP</li>
        <li><span data-color="red">&#9679;</span> War</li>
      </ul>`;
    document.body.appendChild(legend);
  }
  legend.classList.toggle('hidden');
}

// ✅ Toast System
function showToast(msg) {
  let toastEl = document.getElementById('toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.id = 'toast';
    toastEl.className = 'toast-notification';
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 3000);
}
