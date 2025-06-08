/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_home.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';


(async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) window.location.href = 'login.html';

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', async () => {
      await supabase.auth.signOut();
      window.location.href = 'index.html';
    });

    await loadAllianceData(session.user.id);

  } catch (err) {
    console.error('❌ Failed to initialize Alliance Home:', err);
    alert('❌ Failed to load Alliance Home. Please try again.');
    window.location.href = 'play.html';
  }
})();

async function loadAllianceData(userId) {
  try {
    const { data: profile, error: profileError } = await supabase
      .from('users')
      .select('alliance_id')
      .eq('id', userId)
      .single();

    if (profileError) throw new Error('Failed to load profile: ' + profileError.message);
    if (!profile?.alliance_id) {
      alert('You are not in an alliance.');
      return;
    }

    const { data: alliance, error: allianceError } = await supabase
      .from('alliances')
      .select('*')
      .eq('id', profile.alliance_id)
      .single();

    if (allianceError) throw new Error('Failed to load alliance: ' + allianceError.message);
    if (!alliance) {
      alert('Alliance not found.');
      return;
    }

    // Basic details
    document.getElementById('alliance-name').textContent = alliance.name;
    document.getElementById('alliance-leader').textContent = alliance.leader;
    document.getElementById('alliance-status').textContent = alliance.status;
    document.getElementById('alliance-founded')?.textContent = new Date(alliance.created_at).toLocaleDateString();
    document.getElementById('alliance-level')?.textContent = alliance.level ?? '--';
    document.getElementById('alliance-region')?.textContent = alliance.region ?? 'Unspecified';
    document.getElementById('alliance-motd')?.textContent = alliance.motd ?? 'No message set.';
    document.getElementById('alliance-banner-img')?.setAttribute('src', alliance.banner || '../images/default-banner.png');

    // Scores
    document.getElementById('military-score')?.textContent = alliance.military_score ?? '--';
    document.getElementById('economy-score')?.textContent = alliance.economy_score ?? '--';
    document.getElementById('diplomacy-score')?.textContent = alliance.diplomacy_score ?? '--';
    document.getElementById('war-count')?.textContent = alliance.wars_count ?? 0;
    document.getElementById('treaty-count')?.textContent = alliance.treaties_count ?? 0;
    document.getElementById('project-count')?.textContent = alliance.projects_active ?? 0;

    await loadVault(profile.alliance_id);
    await loadMembers(profile.alliance_id);
    await loadProjects(profile.alliance_id);
    await loadContributors(profile.alliance_id);
    await loadAchievements(profile.alliance_id);


  } catch (err) {
    console.error('❌ Error loading Alliance Data:', err);
    alert('❌ Error loading Alliance Data: ' + err.message);
  }
}

async function loadVault(allianceId) {
  const container = document.getElementById('vault-resource-list');
  if (container) container.innerHTML = '<p>Loading vault...</p>';

  try {
    const { data: vault, error } = await supabase
      .from('alliance_vault')
      .select('*')
      .eq('alliance_id', allianceId)
      .single();

    if (error) throw new Error('Failed to load vault: ' + error.message);
    if (!vault) return;

    if (container) container.innerHTML = '';

    Object.entries(vault).forEach(([resource, amount]) => {
      if (['id', 'alliance_id', 'created_at', 'updated_at'].includes(resource)) return;
      const li = document.createElement('li');
      li.innerHTML = `<strong>${resource.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}:</strong> ${amount}`;
      container?.appendChild(li);
    });

    document.getElementById('fortification-level')?.textContent = vault.fortification_level ?? '--';
    document.getElementById('alliance-army-count')?.textContent = vault.army_count ?? '--';


  } catch (err) {
    console.error('❌ Failed to load vault:', err);
    if (container) container.innerHTML = '<p>Failed to load vault.</p>';
  }
}

async function loadMembers(allianceId) {
  const container = document.getElementById('members-list');
  if (container) container.innerHTML = '<tr><td colspan="5">Loading members...</td></tr>';

  try {
    const { data: members, error } = await supabase
      .from('alliance_members')
      .select('*')
      .eq('alliance_id', allianceId);

    if (error) throw new Error('Failed to load members: ' + error.message);

    container.innerHTML = '';

    members.forEach(member => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><img src="../images/crests/${member.crest || 'default.png'}" alt="Crest" class="crest"></td>
        <td>${member.username}</td>
        <td>${member.rank}</td>
        <td>${member.contribution}</td>
        <td>${member.status}</td>`;
      container.appendChild(row);
    });

    document.getElementById('alliance-members-count')?.textContent = members.length;


  } catch (err) {
    console.error('❌ Failed to load members:', err);
    if (container) container.innerHTML = '<tr><td colspan="5">Failed to load members.</td></tr>';
  }
}

async function loadProjects(allianceId) {
  const container = document.getElementById('project-progress-bars');
  if (container) container.innerHTML = '<p>Loading projects...</p>';

  try {
    const { data: projects, error } = await supabase
      .from('projects_alliance')
      .select('*')
      .eq('alliance_id', allianceId);

    if (error) throw new Error('Failed to load projects: ' + error.message);

    container.innerHTML = '';

    projects.forEach(project => {
      const div = document.createElement('div');
      div.classList.add('project-bar');
      div.innerHTML = `<label>${project.name}</label><progress value="${project.progress}" max="100"></progress> <span>${project.progress}%</span>`;
      container.appendChild(div);
    });


  } catch (err) {
    console.error('❌ Failed to load projects:', err);
    if (container) container.innerHTML = '<p>Failed to load projects.</p>';
  }
}

async function loadContributors(allianceId) {
  const container = document.getElementById('top-contributors');
  if (container) container.innerHTML = '<p>Loading contributors...</p>';

  try {
    const { data: top, error } = await supabase
      .from('alliance_members')
      .select('*')
      .eq('alliance_id', allianceId)
      .order('contribution', { ascending: false })
      .limit(5);

    if (error) throw new Error('Failed to load contributors: ' + error.message);

    container.innerHTML = '';

    top.forEach(member => {
      const li = document.createElement('li');
      li.textContent = `${member.username}: ${member.contribution}`;
      container.appendChild(li);
    });


  } catch (err) {
    console.error('❌ Failed to load contributors:', err);
    if (container) container.innerHTML = '<p>Failed to load contributors.</p>';
  }
}

async function loadAchievements(allianceId) {
  const list = document.getElementById('achievements-list');
  if (list) list.innerHTML = '<li>Loading achievements...</li>';

  try {
    const { data, error } = await supabase
      .from('alliance_achievements')
      .select('awarded_at, alliance_achievement_catalogue(name, description)')
      .eq('alliance_id', allianceId)
      .order('awarded_at', { ascending: false });

    if (error) throw new Error('Failed to load achievements: ' + error.message);

    list.innerHTML = '';

    if (!data || data.length === 0) {
      list.innerHTML = '<li>No achievements earned yet.</li>';
      return;
    }

    data.forEach(row => {
      const li = document.createElement('li');
      const ach = row.alliance_achievement_catalogue;
      li.innerHTML = `<strong>${escapeHTML(ach.name)}</strong> - ${escapeHTML(ach.description)} (${new Date(row.awarded_at).toLocaleDateString()})`;
      list.appendChild(li);
    });

  } catch (err) {
    console.error('❌ Failed to load achievements:', err);
    if (list) list.innerHTML = '<li>Failed to load achievements.</li>';
  }
}

function escapeHTML(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
