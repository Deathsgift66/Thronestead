import { supabase } from './supabaseClient.js';

async function loadProjects() {
  const availableList = document.getElementById('available-projects-list');
  const activeList = document.getElementById('active-projects-list');
  const powerScoreEl = document.getElementById('power-score');

  availableList.innerHTML = '<p>Loading...</p>';
  activeList.innerHTML = '<p>Loading...</p>';
  powerScoreEl.textContent = 'Loading...';

  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('Not authenticated');

    const { data: userRow } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();
    const kingdomId = userRow.kingdom_id;

    const { data: resources } = await supabase
      .from('kingdom_resources')
      .select('*')
      .eq('kingdom_id', kingdomId)
      .single();

    const { data: catalogue } = await supabase
      .from('project_player_catalogue')
      .select('*')
      .eq('is_active', true);

    const { data: activeProjects } = await supabase
      .from('projects_player')
      .select('*')
      .eq('kingdom_id', kingdomId);

    const powerScore = activeProjects.reduce((s,p)=>s+(p.power_score||0),0);
    powerScoreEl.textContent = powerScore;

    const activeCodes = activeProjects.map(p=>p.project_code);

    availableList.innerHTML = '';
    (catalogue||[]).forEach(proj=>{
      if (proj.expires_at && new Date(proj.expires_at) < new Date()) return;
      const card = document.createElement('div');
      const canAfford = Object.entries(proj.cost||{}).every(([res,val]) => (resources[res]||0) >= val);
      const active = activeCodes.includes(proj.project_code);
      card.className = 'project-card';
      card.innerHTML = `
        <h3>${proj.name}</h3>
        <p>${proj.description}</p>
        <p>Cost: ${formatCost(proj.cost)}</p>
        <button class="action-btn start" data-code="${proj.project_code}" ${active||!canAfford?'disabled':''}>${active?'Active':canAfford?'Start':'Insufficient Resources'}</button>
      `;
      availableList.appendChild(card);
    });

    document.querySelectorAll('.start').forEach(btn=>{
      btn.addEventListener('click', async ()=>{
        const code = btn.dataset.code;
        const res = await fetch('/api/account-projects/start', {
          method:'POST',
          headers:{'Content-Type':'application/json','X-User-Id':user.id},
          body: JSON.stringify({project_code: code})
        });
        const out = await res.json();
        if(!res.ok) return alert(out.detail||'Failed');
        alert(out.message);
      });
    });

    activeList.innerHTML = '';
    activeProjects.forEach(proj=>{
      const card = document.createElement('div');
      card.className = 'project-card';
      card.innerHTML = `<h3>${proj.project_code}</h3><p>Power: ${proj.power_score}</p>`;
      activeList.appendChild(card);
    });
  } catch(err) {
    console.error(err);
    availableList.innerHTML = '<p>Error loading projects.</p>';
    activeList.innerHTML = '<p>Error loading projects.</p>';
    powerScoreEl.textContent = 'Error';
  }
}

function formatCost(cost){
  if(!cost) return 'None';
  return Object.entries(cost).map(([k,v])=>`${v} ${k}`).join(', ');
}

document.addEventListener('DOMContentLoaded', ()=>{
  loadProjects();
  supabase.channel('projects_player')
    .on('postgres_changes',{event:'*',schema:'public',table:'projects_player'}, ()=> loadProjects())
    .subscribe();

  document.querySelectorAll('.tab-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
    });
  });
});
