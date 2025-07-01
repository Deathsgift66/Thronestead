// Project Name: Thronestead©
// File Name: alliance_members.js
// Version 7.01.2025.08.00
// Developer: Codex (KISS Optimized)

import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';

const RANK_TOOLTIPS = {
  Leader: 'Alliance leader with full authority',
  'Co-Leader': 'Second in command',
  'War Officer': 'Manages wartime efforts',
  Diplomat: 'Handles treaties and diplomacy',
  Member: 'Standard member'
};

const rankPower = ['Member', 'Diplomat', 'War Officer', 'Co-Leader', 'Leader'];
let members = [];
let membersChannel = null;

// 🚀 On Page Load
document.addEventListener('DOMContentLoaded', async () => {
  if (!(await enforceAllianceOrAdminAccess())) return;

  const sortBy = document.getElementById('sort-by')?.value || 'username';
  const direction = document.getElementById('sort-direction')?.value || 'asc';
  await fetchMembers(sortBy, direction);

  setupUIControls();
  setupRealtime();
});

// 🔐 Access Control
async function enforceAllianceOrAdminAccess() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return redirectToLogin();

    const [admin, alliance] = await Promise.all([
      supabase.from('users').select('is_admin').eq('user_id', user.id).single(),
      supabase.from('alliance_members').select('user_id').eq('user_id', user.id).maybeSingle()
    ]);

    if (admin.data?.is_admin || alliance.data) return true;
    alert('You must be in an alliance or be an admin to access this page.');
    window.location.href = 'overview.html';
    return false;
  } catch (err) {
    console.error('❌ Access check error:', err);
    window.location.href = 'overview.html';
    return false;
  }
}

function redirectToLogin() {
  window.location.href = 'login.html';
  return false;
}

// 📦 Member Fetch
async function fetchMembers(sortBy = 'username', direction = 'asc', search = '') {
  const tbody = document.getElementById('members-list');
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="11">Loading members...</td></tr>`;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const url = new URL('/api/alliance/members', window.location.origin);
    url.searchParams.set('sort_by', sortBy);
    url.searchParams.set('direction', direction);
    if (search) url.searchParams.set('search', search);

    const res = await fetch(url, { headers: { 'X-User-ID': user.id } });
    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    members = await res.json();
    renderMembers(members);
  } catch (err) {
    console.error('❌ Member fetch error:', err);
    tbody.innerHTML = `<tr><td colspan="11">Failed to load members.</td></tr>`;
  }
}

// 🔎 Controls
function setupUIControls() {
  document.getElementById('apply-sort')?.addEventListener('click', () => {
    const keyword = document.getElementById('member-search')?.value.toLowerCase() || '';
    const sortBy = document.getElementById('sort-by')?.value || 'username';
    const direction = document.getElementById('sort-direction')?.value || 'asc';
    fetchMembers(sortBy, direction, keyword);
  });
}

// 📡 Realtime Sub
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

// 👥 Render
async function renderMembers(data) {
  const tbody = document.getElementById('members-list');
  if (!tbody) return;

  tbody.innerHTML = '';

  const { isAdmin, userRank, userId } = await getUserPrivileges();

  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="11" class="empty-state">No matching members found.</td></tr>`;
    return;
  }

  const rankLevel = r => rankPower.indexOf(r || 'Member');

  data.forEach(member => {
    const row = document.createElement('tr');
    if (member.rank === 'Leader') row.classList.add('leader-row');

    const canManage = isAdmin || rankLevel(userRank) > rankLevel(member.rank);
    const showFull = member.same_alliance;

    row.innerHTML = `
      <td><img src="../assets/crests/${escapeHTML(member.crest || 'default.png')}" class="crest-icon" alt="Crest"></td>
      <td><a href="kingdom_profile.html?kingdom_id=${member.kingdom_id}">${escapeHTML(member.username)}</a>${member.is_vip ? ' ⭐' : ''}</td>
      <td title="${escapeHTML(RANK_TOOLTIPS[member.rank] || '')}">${escapeHTML(member.rank)}</td>
      <td>${showFull ? roleBadge(member) : '—'}</td>
      <td>${showFull ? escapeHTML(member.status) : '—'}</td>
      <td>${showFull ? member.contribution : '—'}</td>
      <td>${showFull ? member.economy_score : '—'}</td>
      <td>${showFull ? member.military_score : '—'}</td>
      <td>${showFull ? member.diplomacy_score : '—'}</td>
      <td>${showFull ? member.total_output : '—'}</td>
      <td>${canManage ? renderActions(member, userRank.toLowerCase()) : '—'}</td>
    `;

    tbody.appendChild(row);
  });

  tbody.addEventListener('click', e => {
    const btn = e.target.closest('button');
    if (!btn) return;

    const userId = btn.dataset.id;
    if (btn.classList.contains('promote-btn')) promoteMember(userId);
    else if (btn.classList.contains('demote-btn')) demoteMember(userId);
    else if (btn.classList.contains('kick-btn')) removeMember(userId);
    else if (btn.classList.contains('transfer-btn')) transferLeadership(userId);
  }, { once: true });
}

// 🧠 Privileges
async function getUserPrivileges() {
  const { data: { user } } = await supabase.auth.getUser();
  const [admin, rank] = await Promise.all([
    supabase.from('users').select('is_admin').eq('user_id', user.id).single(),
    supabase.from('alliance_members').select('rank').eq('user_id', user.id).maybeSingle()
  ]);
  return {
    isAdmin: admin.data?.is_admin || false,
    userRank: rank.data?.rank || '',
    userId: user.id
  };
}

// 🧩 UI Utils
function renderActions(member, currentRole) {
  const actions = [];
  if (currentRole === 'leader') {
    if (member.rank.toLowerCase() !== 'leader') {
      actions.push(`<button data-id="${member.user_id}" class="promote-btn">Promote</button>`);
      actions.push(`<button data-id="${member.user_id}" class="demote-btn">Demote</button>`);
      actions.push(`<button data-id="${member.user_id}" class="kick-btn danger-btn">Kick</button>`);
      actions.push(`<button data-id="${member.user_id}" class="transfer-btn">Transfer Leadership</button>`);
    }
  } else if (currentRole === 'officer' && member.rank.toLowerCase() === 'member') {
    actions.push(`<button data-id="${member.user_id}" class="promote-btn">Promote</button>`);
    actions.push(`<button data-id="${member.user_id}" class="kick-btn">Kick</button>`);
  }
  return actions.join(' ');
}

function roleBadge(member) {
  const cls = (member.rank || '').toLowerCase().replace(/\s+/g, '-');
  const icons = { leader: '👑', officer: '🛡' };
  const icon = icons[cls] || '';
  const label = member.role || member.rank || '';
  return `<span class="badge role-badge ${cls}">${icon ? icon + ' ' : ''}${escapeHTML(label)}</span>`;
}

// 🛠️ Actions
async function confirmAndPost(endpoint, payload, successMsg, hardConfirm = false) {
  const confirmed = confirm(hardConfirm
    ? 'Are you sure? This cannot be undone.'
    : 'Are you sure you want to proceed?');
  if (!confirmed) return;

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': user.id
      },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
    alert(`✅ ${successMsg}`);
    fetchMembers();
  } catch (err) {
    console.error('❌ Action failed:', err);
    alert(`❌ Failed: ${err.message}`);
  }
}

const promoteMember = id => confirmAndPost('/api/alliance_members/promote', { user_id: id }, 'Member promoted.');
const demoteMember = id => confirmAndPost('/api/alliance_members/demote', { user_id: id }, 'Member demoted.');
const removeMember = id => confirmAndPost('/api/alliance_members/remove', { user_id: id }, 'Member removed.', true);
const transferLeadership = id => confirmAndPost('/api/alliance_members/transfer_leadership', { new_leader_id: id }, 'Leadership transferred.');
