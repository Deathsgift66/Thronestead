/*
Project Name: Kingmakers Rise Frontend
File Name: alliance_members.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';


// Enforce that user is alliance member or admin
async function enforceAllianceOrAdminAccess() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return window.location.href = 'login.html';

    const { data: adminCheck } = await supabase
      .from('users')
      .select('is_admin')
      .eq('user_id', user.id)
      .single();

    if (adminCheck?.is_admin) return true;

    const { data: allianceCheck } = await supabase
      .from('alliance_members')
      .select('user_id')
      .eq('user_id', user.id)
      .maybeSingle();

    if (!allianceCheck) {
      alert("You must be in an alliance (or be an admin) to access this page.");
      window.location.href = 'overview.html';
      return false;
    }

    return true;
  } catch (err) {
    console.error('❌ Error checking access:', err);
    window.location.href = 'overview.html';
    return false;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const accessGranted = await enforceAllianceOrAdminAccess();
  if (!accessGranted) return;

  await fetchMembers();
  setupRealtime();
  setupUIControls();
  setupLogout();
});

let members = [];
let membersChannel;

async function fetchMembers() {
  const tbody = document.getElementById('members-list');
  tbody.innerHTML = `<tr><td colspan="10">Loading members...</td></tr>`;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/alliance-members/view', {
      headers: { 'X-User-ID': user.id }
    });
    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const json = await res.json();
    members = json.alliance_members;
    renderMembers(members);

  } catch (err) {
    console.error('❌ Error loading members:', err);
    tbody.innerHTML = `<tr><td colspan="5">Failed to load members.</td></tr>`;
  }
}

async function getUserPrivileges() {
  const { data: { user } } = await supabase.auth.getUser();

  const [adminRes, rankRes] = await Promise.all([
    supabase.from('users').select('is_admin').eq('user_id', user.id).single(),
    supabase.from('alliance_members').select('rank').eq('user_id', user.id).maybeSingle()
  ]);

  return {
    isAdmin: adminRes.data?.is_admin || false,
    userRank: rankRes.data?.rank || null
  };
}

async function renderMembers(data) {
  const tbody = document.getElementById('members-list');
  tbody.innerHTML = '';
  const { isAdmin, userRank } = await getUserPrivileges();
  const rankPower = ['Member', 'Diplomat', 'War Officer', 'Co-Leader', 'Leader'];

  data.forEach(member => {
    const canManage = isAdmin || rankPower.indexOf(userRank) > rankPower.indexOf(member.rank);
    const row = document.createElement('tr');
    const showFull = member.same_alliance;

    row.innerHTML = `
      <td data-label="Name"><a href="kingdom_profile.html?kingdom_id=${member.kingdom_id}">${member.username}</a>${member.is_vip ? ' ⭐' : ''}</td>
      <td data-label="Rank">${member.rank}</td>
      <td data-label="Role">${showFull ? (member.role || '—') : '—'}</td>
      <td data-label="Status">${showFull ? member.status : '—'}</td>
      <td data-label="Contribution">${showFull ? member.contribution : '—'}</td>
      <td data-label="Economy">${showFull ? member.economy_score : '—'}</td>
      <td data-label="Military">${showFull ? member.military_score : '—'}</td>
      <td data-label="Diplomacy">${showFull ? member.diplomacy_score : '—'}</td>
      <td data-label="Output">${showFull ? member.total_output : '—'}</td>
      <td data-label="Actions">
        ${canManage ? `
          <button onclick="promoteMember('${member.user_id}')">⬆️</button>
          <button onclick="demoteMember('${member.user_id}')">⬇️</button>
          <button onclick="removeMember('${member.user_id}')">❌</button>
        ` : '—'}
      </td>
    `;
    tbody.appendChild(row);
  });
}

function setupUIControls() {
  document.getElementById('apply-sort').addEventListener('click', () => {
    const keyword = document.getElementById('member-search').value.toLowerCase();
    const sortBy = document.getElementById('sort-by').value;
    const direction = document.getElementById('sort-direction').value;

    let filtered = members.filter(m => m.username.toLowerCase().includes(keyword));

    filtered.sort((a, b) => {
      const numericFields = ['contribution','military_score','economy_score','diplomacy_score','total_output'];
      if (numericFields.includes(sortBy)) {
        const valA = Number(a[sortBy] || 0);
        const valB = Number(b[sortBy] || 0);
        return direction === 'asc' ? valA - valB : valB - valA;
      }
      return direction === 'asc'
        ? ('' + a[sortBy]).localeCompare(b[sortBy])
        : ('' + b[sortBy]).localeCompare(a[sortBy]);
    });

    renderMembers(filtered);
  });
}

function setupRealtime() {
  membersChannel = supabase
    .channel('public:alliance_members')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'alliance_members' }, payload => {
      fetchMembers();
    })
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (membersChannel) supabase.removeChannel(membersChannel);
  });
}

async function promoteMember(userId) {
  if (!confirm('Are you sure you want to promote this member?')) return;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/alliance_members/promote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
      body: JSON.stringify({ user_id: userId })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    alert('✅ Member promoted.');
    fetchMembers();

  } catch (err) {
    console.error('❌ Promote failed:', err);
    alert('❌ Promote failed: ' + err.message);
  }
}

async function demoteMember(userId) {
  if (!confirm('Are you sure you want to demote this member?')) return;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/alliance_members/demote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
      body: JSON.stringify({ user_id: userId })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    alert('✅ Member demoted.');
    fetchMembers();

  } catch (err) {
    console.error('❌ Demote failed:', err);
    alert('❌ Demote failed: ' + err.message);
  }
}

async function removeMember(userId) {
  if (!confirm('Are you sure you want to REMOVE this member? This cannot be undone.')) return;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/alliance_members/remove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
      body: JSON.stringify({ user_id: userId })
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    alert('✅ Member removed.');
    fetchMembers();

  } catch (err) {
    console.error('❌ Remove failed:', err);
    alert('❌ Remove failed: ' + err.message);
  }
}

function setupLogout() {
  const logoutBtn = document.getElementById('logout-btn');
  if (!logoutBtn) return;
  logoutBtn.addEventListener('click', async () => {
    await supabase.auth.signOut();
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = 'index.html';
  });
}
