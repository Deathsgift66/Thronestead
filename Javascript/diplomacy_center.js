// Project Name: Thronestead©
// File Name: diplomacy_center.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML } from './utils.js';

let treatyChannel = null;
let userId = null;
let allianceId = null;

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
    const res = await fetch(`https://thronestead.onrender.com/api/diplomacy/metrics/${allianceId}`);
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
  const base = `https://thronestead.onrender.com/api/diplomacy/treaties/${allianceId}`;
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

    if (t.status === 'proposed') {
      actionButtons.push(createActionBtn(t.treaty_id, 'accept'));
      actionButtons.push(createActionBtn(t.treaty_id, 'reject'));
    } else if (t.status === 'active') {
      actionButtons.push(createActionBtn(t.treaty_id, 'cancel'));
    } else if (t.status === 'expired') {
      actionButtons.push(createActionBtn(t.treaty_id, 'renew'));
    }

    row.innerHTML = `
      <td>${escapeHTML(t.treaty_type)}</td>
      <td>${escapeHTML(t.partner_name)}</td>
      <td>${escapeHTML(t.status)}</td>
      <td>${formatDate(t.signed_at)}</td>
      <td>${formatDate(t.end_date)}</td>
      <td>${actionButtons.map(btn => btn.outerHTML).join(' ')}</td>
    `;
    tbody.appendChild(row);
  });

  // Rebind click handlers
  tbody.querySelectorAll('button[data-id]').forEach(btn => {
    btn.addEventListener('click', () => respondTreaty(btn.dataset.id, btn.dataset.action));
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

    const res = await fetch('https://thronestead.onrender.com/api/diplomacy/treaty/propose', {
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

// ✅ Treaty Response Handler
async function respondTreaty(treatyId, action) {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;

  const endpoint = action === 'renew'
    ? 'https://thronestead.onrender.com/api/diplomacy/renew_treaty'
    : 'https://thronestead.onrender.com/api/diplomacy/treaty/respond';

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

function formatDate(val) {
  return val ? new Date(val).toLocaleDateString() : '';
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
