// Project Name: Kingmakers Rise©
// File Name: alliance_members.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

const RANK_TOOLTIPS = {
  Leader: 'Alliance leader with full authority',
  'Co-Leader': 'Second in command',
  'War Officer': 'Manages wartime efforts',
  Diplomat: 'Handles treaties and diplomacy',
  Member: 'Standard member'
};

let members = [];
let membersChannel = null;

document.addEventListener('DOMContentLoaded', async () => {
  const accessGranted = await enforceAllianceOrAdminAccess();
  if (!accessGranted) return;

  await fetchMembers();
  setupRealtime();
  setupUIControls();
  setupLogout();
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
async function fetchMembers() {
  const tbody = document.getElementById('members-list');
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="11">Loading members...</td></tr>`;

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

  data.forEach(member => {
    const row = document.createElement('tr');
    if (member.rank === 'Leader') row.classList.add('leader-row');

    const canManage = isAdmin || rankPower.indexOf(userRank) > rankPower.indexOf(member.rank);
    const showFull = member.same_alliance;

    row.innerHTML = `
      <td><img src="../images/crests/${escapeHTML(member.crest || 'default.png')}" class="crest-icon" alt="Crest"></td>
      <td><a href="kingdom_profile.html?kingdom_id=${member.kingdom_id}">${escapeHTML(member.username)}</a>${member.is_vip ? ' ⭐' : ''}</td>
      <td title="${escapeHTML(RANK_TOOLTIPS[member.rank] || '')}">${escapeHTML(member.rank)}</td>
      <td>${showFull ? escapeHTML(member.role || '—') : '—'}</td>
      <td>${showFull ? escapeHTML(member.status) : '—'}</td>
      <td>${showFull ? member.contribution : '—'}</td>
      <td>${showFull ? member.economy_score : '—'}</td>
      <td>${showFull ? member.military_score : '—'}</td>
      <td>${showFull ? member.diplomacy_score : '—'}</td>
      <td>${showFull ? member.total_output : '—'}</td>
      <td>
        ${canManage ? `
          <button onclick="promoteMember('${member.user_id}')">⬆️</button>
          <button onclick="demoteMember('${member.user_id}')">⬇️</button>
          <button onclick="removeMember('${member.user_id}')">❌</button>
          ${isLeader && member.user_id !== userId ? `<button onclick="transferLeadership('${member.user_id}')">👑</button>` : ''}
        ` : '—'}
      </td>
    `;
    tbody.appendChild(row);
  });
}

// 🔃 Setup sorting & filtering UI
function setupUIControls() {
  document.getElementById('apply-sort')?.addEventListener('click', () => {
    const keyword = document.getElementById('member-search')?.value.toLowerCase() || '';
    const sortBy = document.getElementById('sort-by')?.value;
    const direction = document.getElementById('sort-direction')?.value || 'asc';

    const filtered = members
      .filter(m => m.username.toLowerCase().includes(keyword))
      .sort((a, b) => {
        const num = ['contribution','military_score','economy_score','diplomacy_score','total_output'].includes(sortBy);
        const valA = num ? Number(a[sortBy] || 0) : String(a[sortBy] || '');
        const valB = num ? Number(b[sortBy] || 0) : String(b[sortBy] || '');
        return direction === 'asc' ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
      });

    renderMembers(filtered);
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
    }, fetchMembers)
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

// 🚪 Logout logic
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

// 🛡 Escape user-generated content
function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
