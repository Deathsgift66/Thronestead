// Project Name: Thronestead©
// File Name: preplan_editor.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
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
  let channel = null;
  let plan = {};

  // ✅ Render the battlefield grid
  function renderGrid() {
    grid.innerHTML = '';
    for (let y = 0; y < 20; y++) {
      for (let x = 0; x < 60; x++) {
        const tile = document.createElement('div');
        tile.className = 'grid-tile';
        tile.dataset.x = x;
        tile.dataset.y = y;

        // Highlight based on current plan
        if (plan.patrol_path?.some(p => p.x === x && p.y === y)) {
          tile.classList.add('path');
        }
        if (plan.fallback_point?.x === x && plan.fallback_point?.y === y) {
          tile.classList.add('fallback');
        }

        tile.addEventListener('click', () => handleTileClick(x, y));
        grid.appendChild(tile);
      }
    }
  }

  // ✅ Handle tile click based on current mode
  function handleTileClick(x, y) {
    if (editMode === 'fallback') {
      plan.fallback_point = { x, y };
    } else if (editMode === 'path') {
      plan.patrol_path ??= [];
      plan.patrol_path.push({ x, y });
    }
    updatePlanArea();
    renderGrid();
  }

  // ✅ Sync JSON view with plan object
  function updatePlanArea() {
    planArea.value = JSON.stringify(plan, null, 2);
  }

  // ✅ Load the pre-existing plan for this war
  async function loadPlan() {
    const warId = warInput.value;
    if (!warId) return;
    try {
      const res = await fetch(`https://thronestead.onrender.com/api/alliance-wars/preplan?alliance_war_id=${warId}`);
      const data = await res.json();
      plan = data.plan || {};
      updatePlanArea();
      renderGrid();
    } catch (err) {
      console.error('❌ Failed to load preplan:', err);
    }
  }

  // ✅ Update scoreboard display
  async function updateScoreDisplay(score) {
    if (score) {
      scoreDiv.textContent = `${score.attacker_score} - ${score.defender_score}`;
    }
  }

  // ✅ Subscribe to live score updates via Supabase channel
  async function loadScore() {
    const warId = warInput.value;
    if (!warId) return;
    try {
      const { data, error } = await supabase
        .from('alliance_war_scores')
        .select('attacker_score, defender_score')
        .eq('alliance_war_id', warId)
        .single();
      if (!error) updateScoreDisplay(data);

      if (channel) await channel.unsubscribe();

      channel = supabase
        .channel('war_scores_' + warId)
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'alliance_war_scores',
            filter: `alliance_war_id=eq.${warId}`
          },
          payload => updateScoreDisplay(payload.new)
        )
        .subscribe();
    } catch (err) {
      console.error('❌ Failed to load score:', err);
    }
  }

  // ✅ Button bindings
  fallbackBtn.addEventListener('click', () => { editMode = 'fallback'; });
  pathBtn.addEventListener('click', () => { editMode = 'path'; });
  clearPathBtn.addEventListener('click', () => {
    plan.patrol_path = [];
    renderGrid();
    updatePlanArea();
  });

  // ✅ Listen for manual JSON edits
  planArea.addEventListener('input', () => {
    try {
      plan = JSON.parse(planArea.value || '{}');
      renderGrid();
    } catch {
      // Invalid JSON in textarea - ignore and wait for valid parse
    }
  });

  // ✅ Save the preplan to backend
  saveBtn.addEventListener('click', async () => {
    const warId = parseInt(warInput.value, 10);
    if (!warId) return alert('Enter valid War ID');

    try {
      const res = await fetch('https://thronestead.onrender.com/api/alliance-wars/preplan/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          alliance_war_id: warId,
          preplan_jsonb: plan
        })
      });

      if (!res.ok) throw new Error('Save failed');
      alert('✅ Plan saved!');
    } catch (err) {
      console.error('❌ Error saving plan:', err);
      alert('❌ Save failed.');
    }
  });

  // ✅ Reload plan and score when War ID changes
  warInput.addEventListener('change', async () => {
    await loadPlan();
    await loadScore();
  });

  // ✅ Initial run
  await loadPlan();
  await loadScore();
});
