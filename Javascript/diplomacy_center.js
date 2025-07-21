// Project Name: Thronestead©
// File Name: diplomacy_center.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML, openModal, closeModal, formatDate, capitalize } from './utils.js';

let treatyChannel = null;
let userId = null;
let allianceId = null;
let pendingCancelId = null;

window.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return (window.location.href = 'login.html');
  userId = session.user.id;

  const { data, error } = await supabase
    .from('users')
    .select('alliance_id')
    .eq('user_id', userId)
    .single();
  if (error) {
    console.error('Alliance lookup failed', error);
    return;
  }
  allianceId = data.alliance_id;

  await loadSummary();
  await loadTreaties();

  document.getElementById('confirm-cancel-btn')?.addEventListener('click', () => {
    if (pendingCancelId) respondTreaty(pendingCancelId, 'cancel');
    closeModal('cancel-confirm-modal');
    pendingCancelId = null;
  });
  document.getElementById('dismiss-cancel-btn')?.addEventListener('click', () => {
    closeModal('cancel-confirm-modal');
    pendingCancelId = null;
  });

  // Filter select binding
  document.getElementById('treaty-filter')?.addEventListener('change', loadTreaties);

  // Real-time updates
  treatyChannel = supabase
    .channel('public:alliance_treaties')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'alliance_treaties' }, async () => {
      await loadSummary();
      await loadTreaties();
    })
    .subscribe();
});

window.addEventListener('beforeunload', () => {
  if (treatyChannel) supabase.removeChannel(treatyChannel);
});

// ✅ Summary Stats Loader
async function loadSummary() {
  try {
    const res = await fetch(`/api/diplomacy/metrics/${allianceId}`);
    if (!res.ok) throw new Error('Failed to load summary');
    const data = await res.json();
    document.getElementById('diplomacy-score').textContent = data.diplomacy_score;
    document.getElementById('active-treaties-count').textContent = data.active_treaties;
    document.getElementById('ongoing-wars-count').textContent = data.ongoing_wars;
  } catch (err) {
    console.error('Summary error:', err);
  }
}

// ✅ Treaty Table Loader
async function loadTreaties() {
  const filter = document.getElementById('treaty-filter')?.value || '';
  const base = `/api/diplomacy/treaties/${allianceId}`;
  const url = filter ? `${base}?status=${filter}` : base;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load treaties');
    const data = await res.json();
    renderTreatyTable(data || []);
  } catch (err) {
    console.error('Treaty load error:', err);
  }
}

// ✅ Render Table Body
function renderTreatyTable(treaties) {
  const tbody = document.getElementById('treaty-rows');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (treaties.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">No treaties found.</td></tr>';
    return;
  }

  treaties.forEach(t => {
    const row = document.createElement('tr');
    const actionButtons = [];

    if (t.notes) {
      actionButtons.push(createNotesBtn(t.treaty_id));
    }
    if (t.status === 'proposed') {
      actionButtons.push(createActionBtn(t.treaty_id, 'accept'));
      actionButtons.push(createActionBtn(t.treaty_id, 'reject'));
    } else if (t.status === 'active') {
      actionButtons.push(createActionBtn(t.treaty_id, 'cancel'));
    } else if (t.status === 'expired') {
      actionButtons.push(createActionBtn(t.treaty_id, 'renew'));
    }

    if (t.end_date && t.status === 'active') {
      const diff = new Date(t.end_date) - new Date();
      if (diff > 0 && diff < 604800000) row.classList.add('expiring');
    }

    row.innerHTML = `
      <td>${escapeHTML(t.treaty_type)}</td>
      <td>${escapeHTML(t.partner_name)}</td>
      <td>${escapeHTML(t.status)}</td>
      <td>${formatDate(t.signed_at)}</td>
      <td>${formatDate(t.end_date)}</td>
      <td>${actionButtons.map(btn => btn.outerHTML).join(' ')}</td>
    `;

    const notesRow = document.createElement('tr');
    notesRow.className = 'notes-row';
    notesRow.dataset.notesFor = t.treaty_id;
    notesRow.innerHTML = `<td colspan="6" class="notes-cell">${escapeHTML(t.notes || 'No notes')}</td>`;

    tbody.appendChild(row);
    tbody.appendChild(notesRow);
  });

  // Rebind click handlers
  tbody.querySelectorAll('button[data-id]').forEach(btn => {
    if (btn.dataset.action === 'notes') {
      btn.addEventListener('click', () => toggleNotes(btn.dataset.id));
    } else {
      btn.addEventListener('click', () => handleAction(btn.dataset.id, btn.dataset.action));
    }
  });
}

// ✅ Create Action Button
function createActionBtn(tid, action) {
  const btn = document.createElement('button');
  btn.className = 'btn';
  btn.textContent = capitalize(action);
  btn.dataset.id = tid;
  btn.dataset.action = action;
  return btn;
}

function createNotesBtn(tid) {
  const btn = document.createElement('button');
  btn.className = 'btn';
  btn.textContent = 'Notes';
  btn.dataset.id = tid;
  btn.dataset.action = 'notes';
  return btn;
}

// ✅ Submit Treaty Proposal
export async function proposeTreaty() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  try {
    const payload = {
      proposer_id: allianceId,
      partner_alliance_id: document.getElementById('partner-alliance-id').value,
      treaty_type: document.getElementById('treaty-type').value,
      notes: document.getElementById('treaty-notes').value,
      end_date: document.getElementById('treaty-end').value
    };

    const res = await fetch('/api/diplomacy/treaty/propose', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (!res.ok) throw new Error(result.error || 'Failed to propose treaty');
    alert('Treaty proposal submitted');
  } catch (err) {
    console.error(err);
    alert('Proposal failed');
  }
}

window.proposeTreaty = proposeTreaty;

function handleAction(treatyId, action) {
  if (action === 'cancel') {
    pendingCancelId = treatyId;
    openModal('cancel-confirm-modal');
  } else {
    respondTreaty(treatyId, action);
  }
}

function toggleNotes(tid) {
  const row = document.querySelector(`tr[data-notes-for="${tid}"]`);
  row?.classList.toggle('visible');
}

// ✅ Treaty Response Handler
async function respondTreaty(treatyId, action) {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;

  const endpoint = action === 'renew'
    ? '/api/diplomacy/renew_treaty'
    : '/api/diplomacy/treaty/respond';

  const payload = action === 'renew'
    ? { treaty_id: parseInt(treatyId, 10) }
    : { treaty_id: parseInt(treatyId, 10), response: action };

  try {
    const res = await fetch(endpoint, {
      method: action === 'renew' ? 'POST' : 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || 'Action failed');
    await loadTreaties();
  } catch (err) {
    console.error('Treaty action error:', err);
    alert('Failed to perform action');
  }
}

// ✅ Helpers


