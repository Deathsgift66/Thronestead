import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  const saveBtn = document.getElementById('save-plan');
  const warInput = document.getElementById('war-id');
  const planArea = document.getElementById('preplan-json');
  const grid = document.getElementById('preplan-grid');
  const fallbackBtn = document.getElementById('fallback-mode');
  const pathBtn = document.getElementById('path-mode');
  const clearPathBtn = document.getElementById('clear-path');
  const scoreDiv = document.getElementById('scoreboard-display');
  let editMode = null;
  let channel;
  let plan = {};

  renderGrid();

  function renderGrid() {
    grid.innerHTML = '';
    for (let y = 0; y < 20; y++) {
      for (let x = 0; x < 60; x++) {
        const tile = document.createElement('div');
        tile.className = 'grid-tile';
        tile.dataset.x = x;
        tile.dataset.y = y;
        tile.addEventListener('click', () => handleTile(x, y));
        if (plan.patrol_path?.some(p => p.x === x && p.y === y)) {
          tile.classList.add('path');
        }
        if (plan.fallback_point && plan.fallback_point.x === x && plan.fallback_point.y === y) {
          tile.classList.add('fallback');
        }
        grid.appendChild(tile);
      }
    }
  }

  function handleTile(x, y) {
    if (editMode === 'fallback') {
      plan.fallback_point = { x, y };
    } else if (editMode === 'path') {
      if (!plan.patrol_path) plan.patrol_path = [];
      plan.patrol_path.push({ x, y });
    }
    updatePlanArea();
    renderGrid();
  }

  function updatePlanArea() {
    planArea.value = JSON.stringify(plan, null, 2);
  }

  async function loadPlan() {
    const warId = warInput.value;
    if (!warId) return;
    const res = await fetch(`/api/alliance-wars/preplan?alliance_war_id=${warId}`);
    const data = await res.json();
    plan = data.plan || {};
    updatePlanArea();
    renderGrid();
  }

  async function updateScoreDisplay(score) {
    if (score) {
      scoreDiv.textContent = `${score.attacker_score} - ${score.defender_score}`;
    }
  }

  async function loadScore() {
    const warId = warInput.value;
    if (!warId) return;
    const { data, error } = await supabase
      .from('alliance_war_scores')
      .select('attacker_score, defender_score')
      .eq('alliance_war_id', warId)
      .single();
    if (!error) updateScoreDisplay(data);
    if (channel) await channel.unsubscribe();
    channel = supabase
      .channel('scores')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'alliance_war_scores', filter: `alliance_war_id=eq.${warId}` }, payload => updateScoreDisplay(payload.new))
      .subscribe();
  }

  warInput.addEventListener('change', async () => {
    await loadPlan();
    await loadScore();
  });

  fallbackBtn.addEventListener('click', () => {
    editMode = 'fallback';
  });
  pathBtn.addEventListener('click', () => {
    editMode = 'path';
  });
  clearPathBtn.addEventListener('click', () => {
    plan.patrol_path = [];
    renderGrid();
    updatePlanArea();
  });

  planArea.addEventListener('input', () => {
    try {
      plan = JSON.parse(planArea.value || '{}');
      renderGrid();
    } catch {
      // ignore invalid JSON while typing
    }
  });

  saveBtn.addEventListener('click', async () => {
    const warId = warInput.value;
    if (!warId) return alert('Enter war ID');
    await fetch('/api/alliance-wars/preplan/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alliance_war_id: parseInt(warId, 10), preplan_jsonb: plan })
    });
    alert('Plan saved');
  });

  await loadPlan();
  await loadScore();
});
