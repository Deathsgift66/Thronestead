import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  const saveBtn = document.getElementById('save-plan');
  const warInput = document.getElementById('war-id');
  const planArea = document.getElementById('preplan-json');
  const scoreDiv = document.getElementById('scoreboard-display');
  let channel;

  async function loadPlan() {
    const warId = warInput.value;
    if (!warId) return;
    const res = await fetch(`/api/alliance-wars/preplan?alliance_war_id=${warId}`);
    const data = await res.json();
    planArea.value = JSON.stringify(data.plan || {}, null, 2);
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

  saveBtn.addEventListener('click', async () => {
    const warId = warInput.value;
    if (!warId) return alert('Enter war ID');
    let plan;
    try {
      plan = JSON.parse(planArea.value || '{}');
    } catch {
      alert('Invalid JSON');
      return;
    }
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
