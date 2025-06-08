import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  await loadSpies();
  await loadMissions();
});

async function loadSpies() {
  const infoEl = document.getElementById('spy-info');
  infoEl.textContent = 'Loading...';
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/kingdom/spies', { headers: { 'X-User-ID': user.id } });
    const data = await res.json();
    infoEl.innerHTML = `
      <div>Spy Level: ${data.spy_level}</div>
      <div>Spies: ${data.spy_count} / ${data.max_spy_capacity}</div>
      <div>Progress XP: ${data.spy_xp}</div>
      <div>Upkeep: ${data.spy_upkeep_gold} gold/tick</div>
      <div>Spies Lost: ${data.spies_lost}</div>
      <div>Missions Attempted: ${data.missions_attempted}</div>
      <div>Successful Missions: ${data.missions_successful}</div>
    `;
  } catch (e) {
    infoEl.textContent = 'Failed to load spy info';
  }
}

async function loadMissions() {
  const listEl = document.getElementById('missions');
  listEl.textContent = 'Loading missions...';
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/kingdom/spy_missions', { headers: { 'X-User-ID': user.id } });
    const data = await res.json();
    listEl.innerHTML = '';
    (data.missions || []).forEach(m => {
      const div = document.createElement('div');
      const type = m.mission_type || m.mission;
      div.textContent = `${type} targeting ${m.target_id} - ${m.status}`;
      listEl.appendChild(div);
    });
  } catch (e) {
    listEl.textContent = 'Failed to load missions';
  }
}
