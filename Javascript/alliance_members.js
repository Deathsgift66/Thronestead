// Project Name: Thronestead©
// File Name: alliance_members.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';

const RANK_TOOLTIPS = {
  Leader: 'Alliance leader with full authority',
  'Co-Leader': 'Second in command',
  'War Officer': 'Manages wartime efforts',
  Diplomat: 'Handles treaties and diplomacy',
  Member: 'Standard member'
};

function renderActions(member, currentRole) {
  const actions = [];
  if (currentRole === 'leader') {
    if (member.rank.toLowerCase() !== 'leader') {
      actions.push(`<button data-id="${member.user_id}" class="promote-btn">Promote</button>`);
      actions.push(`<button data-id="${member.user_id}" class="demote-btn">Demote</button>`);
      actions.push(`<button data-id="${member.user_id}" class="kick-btn danger-btn">Kick</button>`);
      actions.push(`<button data-id="${member.user_id}" class="transfer-btn">Transfer Leadership</button>`);
    }
  } else if (currentRole === 'officer') {
    if (member.rank.toLowerCase() === 'member') {
      actions.push(`<button data-id="${member.user_id}" class="promote-btn">Promote</button>`);
      actions.push(`<button data-id="${member.user_id}" class="kick-btn">Kick</button>`);
    }
  }
  return actions.join(' ');
}

function roleBadge(member) {
  if (!member.rank) return '';
  const cls = member.rank.toLowerCase().replace(/\s+/g, '-');
  const icons = { leader: '👑', officer: '🛡' };
  const icon = icons[cls] || '';
  const text = member.role || member.rank;
  return `<span class="badge role-badge ${cls}">${icon ? icon + ' ' : ''}${escapeHTML(text)}</span>`;
}

let members = [];
let membersChannel = null;

document.addEventListener('DOMContentLoaded', async () => {
  const accessGranted = await enforceAllianceOrAdminAccess();
  if (!accessGranted) return;

  const sortBy = document.getElementById('sort-by')?.value || 'username';
  const dir = document.getElementById('sort-direction')?.value || 'asc';
  await fetchMembers(sortBy, dir);
  setupRealtime();
  setupUIControls();
});

// 🔐 Enforce user access to alliance-only pages
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

// 📦 Fetch member list from API
async function fetchMembers(sortBy = 'username', direction = 'asc', search = '') {
  const tbody = document.getElementById('members-list');
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="11">Loading members...</td></tr>`;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const params = new URLSearchParams({ sort_by: sortBy, direction, search });
    const res = await fetch(`/api/alliance/members?${params.toString()}`, {
      headers: { 'X-User-ID': user.id }
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    members = await res.json();
    renderMembers(members);
  } catch (err) {
    console.error('❌ Error loading members:', err);
    tbody.innerHTML = `<tr><td colspan="11">Failed to load members.</td></tr>`;
  }
}

// 👑 Retrieve user privileges for rank-based controls
async function getUserPrivileges() {
  const { data: { user } } = await supabase.auth.getUser();

  const [adminRes, rankRes] = await Promise.all([
    supabase.from('users').select('is_admin').eq('user_id', user.id).single(),
    supabase.from('alliance_members').select('rank').eq('user_id', user.id).maybeSingle()
  ]);

  return {
    isAdmin: adminRes.data?.is_admin || false,
    userRank: rankRes.data?.rank || null,
    userId: user.id
  };
}

// 🧑‍💼 Render members into table
async function renderMembers(data) {
  const tbody = document.getElementById('members-list');
  if (!tbody) return;

  tbody.innerHTML = '';
  const { isAdmin, userRank, userId } = await getUserPrivileges();
  const rankPower = ['Member', 'Diplomat', 'War Officer', 'Co-Leader', 'Leader'];
  const isLeader = userRank === 'Leader';

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" class="empty-state">No matching members found.</td></tr>`;
    return;
  }

  data.forEach(member => {
    const row = document.createElement('tr');
    if (member.rank === 'Leader') row.classList.add('leader-row');

    const canManage = isAdmin || rankPower.indexOf(userRank) > rankPower.indexOf(member.rank);
    const showFull = member.same_alliance;

    row.innerHTML = `
      <td><img src="../images/crests/${escapeHTML(member.crest || 'default.png')}" class="crest-icon" alt="Crest"></td>
      <td><a href="kingdom_profile.html?kingdom_id=${member.kingdom_id}">${escapeHTML(member.username)}</a>${member.is_vip ? ' ⭐' : ''}</td>
      <td title="${escapeHTML(RANK_TOOLTIPS[member.rank] || '')}">${escapeHTML(member.rank)}</td>
      <td>${showFull ? roleBadge(member) : '—'}</td>
      <td>${showFull ? escapeHTML(member.status) : '—'}</td>
      <td>${showFull ? member.contribution : '—'}</td>
      <td>${showFull ? member.economy_score : '—'}</td>
      <td>${showFull ? member.military_score : '—'}</td>
      <td>${showFull ? member.diplomacy_score : '—'}</td>
      <td>${showFull ? member.total_output : '—'}</td>
      <td>
        ${canManage ? renderActions(member, userRank.toLowerCase()) : '—'}
      </td>
    `;
    tbody.appendChild(row);
  });

  tbody.addEventListener('click', evt => {
    const btn = evt.target.closest('button');
    if (!btn) return;
    const id = btn.dataset.id;
    if (btn.classList.contains('promote-btn')) promoteMember(id);
    else if (btn.classList.contains('demote-btn')) demoteMember(id);
    else if (btn.classList.contains('kick-btn')) removeMember(id);
    else if (btn.classList.contains('transfer-btn')) transferLeadership(id);
  }, { once: true });
}

// 🔃 Setup sorting & filtering UI
function setupUIControls() {
  document.getElementById('apply-sort')?.addEventListener('click', () => {
    const keyword = document.getElementById('member-search')?.value.toLowerCase() || '';
    const sortBy = document.getElementById('sort-by')?.value || 'username';
    const direction = document.getElementById('sort-direction')?.value || 'asc';

    fetchMembers(sortBy, direction, keyword);
  });
}

// 🔄 Realtime sync on alliance_members changes
function setupRealtime() {
  membersChannel = supabase
    .channel('public:alliance_members')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'alliance_members'
    }, () => fetchMembers())
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (membersChannel) supabase.removeChannel(membersChannel);
  });
}

// ⚙️ Manage actions: promote/demote/remove/transfer
async function promoteMember(userId) {
  await confirmAndPost('/api/alliance_members/promote', { user_id: userId }, 'Member promoted.');
}

async function demoteMember(userId) {
  await confirmAndPost('/api/alliance_members/demote', { user_id: userId }, 'Member demoted.');
}

async function removeMember(userId) {
  await confirmAndPost('/api/alliance_members/remove', { user_id: userId }, 'Member removed.', true);
}

async function transferLeadership(userId) {
  await confirmAndPost('/api/alliance_members/transfer_leadership', { new_leader_id: userId }, 'Leadership transferred.');
}

async function confirmAndPost(endpoint, payload, successMsg, hardConfirm = false) {
  const confirmed = confirm(hardConfirm
    ? 'Are you sure? This cannot be undone.'
    : `Are you sure you want to proceed?`);

  if (!confirmed) return;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    alert(`✅ ${successMsg}`);
    fetchMembers();
  } catch (err) {
    console.error(`❌ Action failed:`, err);
    alert(`❌ Failed: ${err.message}`);
  }
}

// 🛡 Escape user-generated content
