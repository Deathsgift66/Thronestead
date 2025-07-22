// Project Name: Thronestead©
// File Name: preplan_editor.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { showToast } from './core_utils.js';

document.addEventListener('DOMContentLoaded', async () => {
  const saveBtn = document.getElementById('save-plan');
  const warInput = document.getElementById('war-id');
  const planArea = document.getElementById('preplan-json');
  const jsonWarning = document.getElementById('json-warning');
  const grid = document.getElementById('preplan-grid');
  const fallbackBtn = document.getElementById('fallback-mode');
  const pathBtn = document.getElementById('path-mode');
  const clearPathBtn = document.getElementById('clear-path');
  const clearFallbackBtn = document.getElementById('clear-fallback');
  const undoBtn = document.getElementById('undo-plan');
  const scoreDiv = document.getElementById('scoreboard-display');

  let editMode = null;
  let channel = null;
  let plan = {};
  let lastSavedPlan = {};

  function updateModeButtons() {
    fallbackBtn.classList.toggle('active', editMode === 'fallback');
    pathBtn.classList.toggle('active', editMode === 'path');
  }

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

  function validatePlan(p) {
    if (p.fallback_point) {
      const f = p.fallback_point;
      if (typeof f.x !== 'number' || typeof f.y !== 'number') return false;
    }
    if (p.patrol_path) {
      if (!Array.isArray(p.patrol_path)) return false;
      for (const node of p.patrol_path) {
        if (typeof node.x !== 'number' || typeof node.y !== 'number') return false;
      }
    }
    return true;
  }

  // ✅ Load the pre-existing plan for this war
  async function loadPlan() {
    const warId = warInput.value;
    if (!warId) return;
    try {
      const res = await fetch(`/api/alliance-wars/preplan?alliance_war_id=${warId}`);
      const data = await res.json();
      plan = data.plan || {};
      lastSavedPlan = JSON.parse(JSON.stringify(plan));
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
        .maybeSingle();
      if (!error) updateScoreDisplay(data);

      if (channel?.unsubscribe) await channel.unsubscribe();

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
  fallbackBtn.addEventListener('click', () => {
    editMode = 'fallback';
    updateModeButtons();
  });
  pathBtn.addEventListener('click', () => {
    editMode = 'path';
    updateModeButtons();
  });
  clearPathBtn.addEventListener('click', () => {
    plan.patrol_path = [];
    renderGrid();
    updatePlanArea();
  });
  clearFallbackBtn.addEventListener('click', () => {
    delete plan.fallback_point;
    renderGrid();
    updatePlanArea();
  });
  undoBtn.addEventListener('click', () => {
    plan = JSON.parse(JSON.stringify(lastSavedPlan));
    renderGrid();
    updatePlanArea();
  });

  // ✅ Listen for manual JSON edits
  planArea.addEventListener('input', () => {
    try {
      const parsed = JSON.parse(planArea.value || '{}');
      if (!validatePlan(parsed)) throw new Error('invalid');
      plan = parsed;
      jsonWarning.style.display = 'none';
      renderGrid();
    } catch {
      jsonWarning.textContent = 'Invalid JSON';
      jsonWarning.style.display = 'block';
    }
  });

  // ✅ Save the preplan to backend with simple debounce
  let saveCooldown = false;
  saveBtn.addEventListener('click', async () => {
    if (saveCooldown) return;
    saveCooldown = true;
    saveBtn.disabled = true;
    setTimeout(() => (saveCooldown = false), 1000);
    const warId = parseInt(warInput.value, 10);
    if (!warId) {
      showToast('Enter valid War ID', 'error');
      saveBtn.disabled = false;
      return;
    }
    if (!validatePlan(plan)) {
      showToast('Plan JSON invalid', 'error');
      saveBtn.disabled = false;
      return;
    }

    try {
      const res = await fetch('/api/alliance-wars/preplan/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          alliance_war_id: warId,
          preplan_jsonb: plan
        })
      });

      if (!res.ok) throw new Error('Save failed');
      lastSavedPlan = JSON.parse(JSON.stringify(plan));
      showToast('Plan saved!', 'success');
    } catch (err) {
      console.error('❌ Error saving plan:', err);
      showToast('Save failed', 'error');
    } finally {
      saveBtn.disabled = false;
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
  updateModeButtons();
});
