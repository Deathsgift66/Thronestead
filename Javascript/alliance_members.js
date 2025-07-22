// Project Name: Thronestead©
// File Name: alliance_members.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from './supabaseClient.js';
import { escapeHTML, showToast, toggleLoading, debounce, getCsrfToken } from './core_utils.js';
import { rankLevel, RANK_POWER } from './constants.js';

const RANK_TOOLTIPS = {
  Leader: 'Alliance leader with full authority',
  'Co-Leader': 'Second in command',
  'War Officer': 'Manages wartime efforts',
  Diplomat: 'Handles treaties and diplomacy',
  Member: 'Standard member'
};

let members = [];
let membersChannel = null;
let currentUser = null;
let currentAllianceId = null;
let cachedPrivileges = null;
let currentPage = 1;
const pageSize = 20;
let actionsBound = false;
let fetchController = null;
let authToken = '';
let csrfToken = getCsrfToken();
let fetchInProgress = false;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  authToken = session?.access_token || '';
  const { data: { user } } = await supabase.auth.getUser();
  currentUser = user;
  if (!(await enforceAllianceOrAdminAccess())) return;
  const { allianceId } = await getUserPrivileges();
  currentAllianceId = allianceId;
  const sortBy = document.getElementById('sort-by')?.value || 'username';
  const direction = document.getElementById('sort-direction')?.value || 'asc';
  await fetchMembers(sortBy, direction);
  setupUIControls();
  setupMembersListHandler();
  setupLoadMoreButton();
  setupRealtime();
  setInterval(async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) authToken = session.access_token;
    csrfToken = getCsrfToken();
  }, 45 * 60 * 1000);
});

supabase.auth.onAuthStateChange(async (_event, session) => {
  authToken = session?.access_token || '';
  currentUser = session?.user || null;
  if (!session && membersChannel) {
    await membersChannel.unsubscribe();
    membersChannel = null;
  }
});

async function enforceAllianceOrAdminAccess() {
  try {
    if (!currentUser) return redirectToLogin();
    const [admin, alliance] = await Promise.all([
      supabase.from('users').select('is_admin').eq('user_id', currentUser.id).single(),
      supabase.from('alliance_members').select('user_id').eq('user_id', currentUser.id).maybeSingle()
    ]);
    if (admin.error) console.error(admin.error.message || admin.error);
    if (alliance.error) console.error(alliance.error.message || alliance.error);
    if (admin.data?.is_admin || alliance.data) return true;
    showToast('You must be in an alliance or be an admin to access this page.', 'error');
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

async function fetchMembers(sortBy = 'username', direction = 'asc', search = '', page = 1) {
  if (fetchInProgress && fetchController) fetchController.abort();
  fetchInProgress = true;
  const params = { sortBy, direction, search, page };
  const tbody = document.getElementById('members-list');
  if (!tbody) {
    fetchInProgress = false;
    return;
  }
  tbody.innerHTML = `<tr><td colspan="11"><div class="loading-spinner"></div></td></tr>`;
  toggleLoading(true);
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      redirectToLogin();
      return;
    }
    currentUser = user;
    const url = new URL('/api/alliance/members', window.location.origin);
    const validSort = ['username','rank','contribution','status','military_score','economy_score','diplomacy_score','total_output'];
    if (!validSort.includes(sortBy)) sortBy = 'username';
    const validDir = ['asc','desc'];
    if (!validDir.includes(direction.toLowerCase())) direction = 'asc';
    const sanitizedSearch = search.replace(/[^\w\s-]/g, '').slice(0,50);
    url.searchParams.set('sort_by', sortBy);
    url.searchParams.set('direction', direction);
    url.searchParams.set('offset', (page - 1) * pageSize);
    url.searchParams.set('limit', pageSize);
    if (sanitizedSearch) url.searchParams.set('search', sanitizedSearch);
    fetchController = new AbortController();
    const timeoutId = setTimeout(() => {
      if (fetchController) fetchController.abort();
    }, 15000);
    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-CSRF-Token': csrfToken
      },
      signal: fetchController.signal
    });
    clearTimeout(timeoutId);
    if (res.status === 403) {
      redirectToLogin();
      return;
    }
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const results = await res.json();
    if (page === 1) members = results; else members = members.concat(results);
    updateRoleCounts(members);
    renderMembers(members, page);
  } catch (err) {
    console.error('❌ Member fetch error:', err);
    tbody.innerHTML = `<tr><td colspan="11" class="empty-state">Failed to load members. <button id="retry-fetch">Retry</button></td></tr>`;
    const retryBtn = document.getElementById('retry-fetch');
    if (retryBtn) {
      const { sortBy: s = 'username', direction: d = 'asc', search: q = '', page: p = 1 } = params || {};
      retryBtn.addEventListener('click', () => fetchMembers(s, d, q, p), { once: true });
    }
  } finally {
    toggleLoading(false);
    fetchInProgress = false;
    fetchController = null;
  }
}

function setupUIControls() {
  const btn = document.getElementById('apply-sort');
  if (!btn) return;
  const handler = debounce(async () => {
    btn.disabled = true;
    btn.setAttribute('aria-disabled', 'true');
    const original = btn.textContent;
    btn.innerHTML = '<div class="loading-spinner"></div>';
    currentPage = 1;
    const keyword = document.getElementById('member-search')?.value.toLowerCase() || '';
    const sortBy = document.getElementById('sort-by')?.value || 'username';
    const direction = document.getElementById('sort-direction')?.value || 'asc';
    await fetchMembers(sortBy, direction, keyword);
    btn.disabled = false;
    btn.setAttribute('aria-disabled', 'false');
    btn.textContent = original;
  }, 300);
  btn.addEventListener('click', () => { handler.cancel(); handler(); });
  setupSortableHeaders();
  const searchInput = document.getElementById('member-search');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(async () => {
      currentPage = 1;
      const keyword = searchInput.value.toLowerCase() || '';
      const sortBy = document.getElementById('sort-by')?.value || 'username';
      const direction = document.getElementById('sort-direction')?.value || 'asc';
      await fetchMembers(sortBy, direction, keyword);
    }, 300));
  }
}

function setupSortableHeaders() {
  const activateSort = sortKey => {
    const sortInput = document.getElementById('sort-by');
    const dirInput = document.getElementById('sort-direction');
    let direction = dirInput.value;
    if (sortInput.value === sortKey) {
      direction = direction === 'asc' ? 'desc' : 'asc';
    } else {
      sortInput.value = sortKey;
      direction = 'asc';
    }
    dirInput.value = direction;
    document.querySelectorAll('.members-table th.sortable').forEach(h => h.removeAttribute('aria-sort'));
    const active = document.querySelector(`.members-table th[data-sort="${sortKey}"]`);
    if (active) active.setAttribute('aria-sort', direction === 'asc' ? 'ascending' : 'descending');
    currentPage = 1;
    fetchMembers(sortKey, direction, document.getElementById('member-search')?.value.toLowerCase() || '');
  };

  document.querySelectorAll('.members-table th.sortable').forEach(th => {
    const sortKey = th.dataset.sort;
    if (!sortKey) return;
    th.addEventListener('click', () => activateSort(sortKey));
    th.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        activateSort(sortKey);
      }
    });
  });
  const currentSort = document.getElementById('sort-by')?.value || 'username';
  const dir = document.getElementById('sort-direction')?.value || 'asc';
  const th = document.querySelector(`.members-table th[data-sort="${currentSort}"]`);
  if (th) th.setAttribute('aria-sort', dir === 'asc' ? 'ascending' : 'descending');
}

function setupMembersListHandler() {
  const tbody = document.getElementById('members-list');
  if (!tbody || actionsBound) return;
  tbody.addEventListener('click', async e => {
    const copyBtn = e.target.closest('.copy-btn');
    if (copyBtn) {
      try {
        const name = (copyBtn.dataset.username || '').trim();
        if (name) {
          await navigator.clipboard.writeText(name);
          showToast('Username copied!', 'success');
        }
      } catch (err) {
        console.error('❌ Copy failed:', err);
        showToast('Failed to copy username', 'error');
      }
      return;
    }

    const btn = e.target.closest('button');
    if (!btn || btn.disabled) return;
    const userId = btn.dataset.id;
    btn.disabled = true;
    btn.setAttribute('aria-disabled', 'true');
    try {
      if (btn.classList.contains('promote-btn')) await promoteMember(userId);
      else if (btn.classList.contains('demote-btn')) await demoteMember(userId);
      else if (btn.classList.contains('kick-btn')) await removeMember(userId);
      else if (btn.classList.contains('transfer-btn')) await transferLeadership(userId);
    } finally {
      setTimeout(() => {
        btn.disabled = false;
        btn.setAttribute('aria-disabled', 'false');
      }, 3000);
    }
  });
  actionsBound = true;
}

function setupLoadMoreButton() {
  const btn = document.getElementById('load-more');
  if (!btn) return;
  btn.addEventListener('click', () => {
    currentPage++;
    fetchMembers(
      document.getElementById('sort-by')?.value || 'username',
      document.getElementById('sort-direction')?.value || 'asc',
      document.getElementById('member-search')?.value.toLowerCase() || '',
      currentPage
    );
  });
}

function setupRealtime() {
  if (!currentAllianceId) return;
  let attempt = 0;
  const connect = () => {
    membersChannel = supabase
      .channel('public:alliance_members')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'alliance_members',
          filter: `alliance_id=eq.${currentAllianceId}`
        },
        async () => await fetchMembers()
      )
      .on('error', handleError)
      .on('close', handleError)
      .subscribe(status => {
        if (status === 'SUBSCRIBED') attempt = 0;
      });
  };

  const handleError = () => {
    attempt++;
    const delay = Math.min(30000, 1000 * 2 ** attempt);
    setTimeout(connect, delay);
  };

  connect();

  window.addEventListener('beforeunload', async () => {
    if (membersChannel) {
      await membersChannel.unsubscribe();
      membersChannel = null;
    }
  });
}

async function renderMembers(data, page = currentPage) {
  const tbody = document.getElementById('members-list');
  if (!tbody) return;
  tbody.innerHTML = '';
  const { isAdmin, userRank, userId } = await getUserPrivileges();
  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="11" class="empty-state">No matching members found.</td></tr>`;
    document.getElementById('load-more')?.classList.add('hidden');
    return;
  }

  data.forEach(member => {
    const row = document.createElement('tr');
    if (member.rank === 'Leader') row.classList.add('leader-row');
    if (member.user_id === userId) row.classList.add('highlight-current-user');
    const canManage = isAdmin || rankLevel(userRank) > rankLevel(member.rank);
    const showFull = member.same_alliance;
    row.innerHTML = `
      <td><img src="/Assets/crests/${escapeHTML(member.crest || 'default.png')}" class="crest-icon" alt="${escapeHTML(member.username)} crest" loading="lazy" decoding="async" onerror="this.src='/Assets/crests/default.png'"></td>
      <td><a href="kingdom_profile.html?kingdom_id=${member.kingdom_id}">${escapeHTML(member.username)}</a>${member.is_vip ? ' <span aria-hidden="true">⭐</span><span class="sr-only">VIP</span>' : ''}<button class="copy-btn" data-username="${escapeHTML(member.username)}" aria-label="Copy username ${escapeHTML(member.username)}" title="Copy username">📋</button></td>
      <td title="${escapeHTML(RANK_TOOLTIPS[member.rank] || '')}">${escapeHTML(member.rank)}</td>
      <td>${showFull ? roleBadge(member) : '—'}</td>
      <td title="${escapeHTML(member.status || '')}">${showFull ? escapeHTML(member.status) : '—'}</td>
      <td title="${member.contribution}">${showFull ? member.contribution : '—'}</td>
      <td title="${member.economy_score}">${showFull ? member.economy_score : '—'}</td>
      <td title="${member.military_score}">${showFull ? member.military_score : '—'}</td>
      <td title="${member.diplomacy_score}">${showFull ? member.diplomacy_score : '—'}</td>
      <td title="${member.total_output}">${showFull ? member.total_output : '—'}</td>
      <td>${canManage ? renderActions(member, userRank.toLowerCase(), userId) : '—'}</td>
    `;
    tbody.appendChild(row);
  });

  document.getElementById('load-more')?.classList.toggle('hidden', data.length < pageSize);
  const status = document.getElementById('members-status');
  if (status) status.textContent = page === 1 ? 'Member list updated' : 'More members loaded';
}

function updateRoleCounts(list) {
  const rankHeader = document.getElementById('rank-header');
  const roleHeader = document.getElementById('role-header');
  if (rankHeader) {
    rankHeader.innerHTML = 'Rank';
    const rankCounts = {};
    list.forEach(m => {
      const r = m.rank || 'Unknown';
      rankCounts[r] = (rankCounts[r] || 0) + 1;
    });
    Object.entries(rankCounts).forEach(([rank, count]) => {
      const span = document.createElement('span');
      span.className = 'count-badge';
      span.title = `${rank}: ${count}`;
      span.textContent = count;
      rankHeader.appendChild(span);
    });
  }
  if (roleHeader) {
    roleHeader.innerHTML = 'Role';
    const roleCounts = {};
    list.forEach(m => {
      if (m.role) roleCounts[m.role] = (roleCounts[m.role] || 0) + 1;
    });
    Object.entries(roleCounts).forEach(([role, count]) => {
      const span = document.createElement('span');
      span.className = 'count-badge';
      span.title = `${role}: ${count}`;
      span.textContent = count;
      roleHeader.appendChild(span);
    });
  }
}

async function fetchUserPrivileges() {
  const user = currentUser;
  const [admin, rank] = await Promise.all([
    supabase.from('users').select('is_admin').eq('user_id', user.id).single(),
    supabase.from('alliance_members').select('rank,alliance_id').eq('user_id', user.id).maybeSingle()
  ]);
  if (admin.error) console.error(admin.error.message || admin.error);
  if (rank.error) console.error(rank.error.message || rank.error);
  currentAllianceId = rank.data?.alliance_id || null;
  return {
    isAdmin: admin.data?.is_admin || false,
    userRank: rank.data?.rank || '',
    userId: user.id,
    allianceId: currentAllianceId
  };
}

async function getUserPrivileges() {
  if (!cachedPrivileges) cachedPrivileges = await fetchUserPrivileges();
  return cachedPrivileges;
}

function canManageMember(member, currentRole, currentUserId) {
  if (member.user_id === currentUserId) return false;
  return rankLevel(currentRole) > rankLevel(member.rank);
}

function renderActions(member, currentRole, currentUserId) {
  const actions = [];
  if (!canManageMember(member, currentRole, currentUserId)) return '';
  const memberLevel = rankLevel(member.rank);

  if (currentRole === 'leader') {
    if (member.rank.toLowerCase() !== 'leader') {
      if (memberLevel < RANK_POWER.length - 1) {
        actions.push(`<button data-id="${member.user_id}" class="promote-btn" aria-label="Promote member ${escapeHTML(member.username)}" title="Promote member ${escapeHTML(member.username)}">Promote</button>`);
      }
      if (memberLevel > 0) {
        actions.push(`<button data-id="${member.user_id}" class="demote-btn" aria-label="Demote member ${escapeHTML(member.username)}" title="Demote member ${escapeHTML(member.username)}">Demote</button>`);
      }
      actions.push(`<button data-id="${member.user_id}" class="kick-btn danger-btn" aria-label="Kick member ${escapeHTML(member.username)}" title="Kick member ${escapeHTML(member.username)}">Kick</button>`);
      actions.push(`<button data-id="${member.user_id}" class="transfer-btn" aria-label="Transfer leadership to ${escapeHTML(member.username)}" title="Transfer leadership to ${escapeHTML(member.username)}">Transfer Leadership</button>`);
    }
  } else if (currentRole === 'war officer' && member.rank.toLowerCase() === 'member') {
    actions.push(`<button data-id="${member.user_id}" class="promote-btn" aria-label="Promote member ${escapeHTML(member.username)}" title="Promote member ${escapeHTML(member.username)}">Promote</button>`);
    actions.push(`<button data-id="${member.user_id}" class="kick-btn" aria-label="Kick member ${escapeHTML(member.username)}" title="Kick member ${escapeHTML(member.username)}">Kick</button>`);
  }
  return actions.join(' ');
}

function roleBadge(member) {
  const cls = (member.rank || '')
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '');
  const icons = { leader: '👑', officer: '🛡' };
  const icon = icons[cls] || '';
  const label = member.role || member.rank || '';
  return `<span class="badge role-badge ${cls}">${icon ? `<span aria-hidden="true">${icon}</span> ` : ''}${escapeHTML(label)}<span class="sr-only">${escapeHTML(label)}</span></span>`;
}

async function confirmAndPost(endpoint, payload, successMsg, hardConfirm = false) {
  const confirmed = confirm(hardConfirm ? 'Are you sure? This cannot be undone.' : 'Are you sure you want to proceed?');
  if (!confirmed) return;
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authToken}`,
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify(payload)
    });
    if (res.status === 403) {
      redirectToLogin();
      return;
    }
    if (!res.ok) throw new Error(await res.text());
    showToast(`✅ ${successMsg}`, 'success');
    fetchMembers();
  } catch (err) {
    console.error('❌ Action failed:', err);
    showToast(`❌ Failed: ${err.message}`, 'error');
  }
}

const promoteMember = id => confirmAndPost('/api/alliance_members/promote', { user_id: id }, 'Member promoted.');
const demoteMember = id => confirmAndPost('/api/alliance_members/demote', { user_id: id }, 'Member demoted.');
const removeMember = id => confirmAndPost('/api/alliance_members/remove', { user_id: id }, 'Member removed.', true);
const transferLeadership = id => {
  const confirmName = prompt('Type TRANSFER to confirm leadership transfer:');
  if (!confirmName || confirmName.trim().toUpperCase() !== 'TRANSFER') return;
  confirmAndPost('/api/alliance_members/transfer_leadership', { new_leader_id: id }, 'Leadership transferred.', true);
};
