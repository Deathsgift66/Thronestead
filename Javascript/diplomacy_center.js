import { supabase } from './supabaseClient.js';

let treatyChannel;

window.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  const uid = session.user.id;
  await loadSummary(uid);
  await loadTreaties(uid);

  document.getElementById('treaty-filter').addEventListener('change', () => {
    loadTreaties(uid);
  });

  treatyChannel = supabase
    .channel('public:alliance_treaties')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'alliance_treaties' }, async () => {
      await loadSummary(uid);
      await loadTreaties(uid);
    })
    .subscribe();
});

window.addEventListener('beforeunload', () => {
  if (treatyChannel) supabase.removeChannel(treatyChannel);
});

async function loadSummary(uid) {
  const res = await fetch('/api/diplomacy/summary', { headers: { 'X-User-ID': uid } });
  if (!res.ok) return;
  const data = await res.json();
  document.getElementById('diplomacy-score').textContent = data.diplomacy_score;
  document.getElementById('active-treaties-count').textContent = data.active_treaties;
  document.getElementById('ongoing-wars-count').textContent = data.ongoing_wars;
}

async function loadTreaties(uid) {
  const filter = document.getElementById('treaty-filter').value;
  const url = filter ? `/api/diplomacy/treaties?filter=${filter}` : '/api/diplomacy/treaties';
  const res = await fetch(url, { headers: { 'X-User-ID': uid } });
  if (!res.ok) return;
  const data = await res.json();
  const tbody = document.getElementById('treaty-rows');
  tbody.innerHTML = '';
  data.forEach(t => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${t.treaty_type}</td>
      <td>${t.partner_name}</td>
      <td>${t.status}</td>
      <td>${t.signed_at ? new Date(t.signed_at).toLocaleDateString() : ''}</td>
      <td>${t.end_date ? new Date(t.end_date).toLocaleDateString() : ''}</td>
      <td>
        ${t.status === 'proposed' ? `
          <button class="btn" data-id="${t.treaty_id}" data-action="accept">Accept</button>
          <button class="btn" data-id="${t.treaty_id}" data-action="reject">Reject</button>
        ` : ''}
        ${t.status === 'active' ? `
          <button class="btn" data-id="${t.treaty_id}" data-action="cancel">Cancel</button>
        ` : ''}
        ${t.status === 'expired' ? `
          <button class="btn" data-id="${t.treaty_id}" data-action="renew">Renew</button>
        ` : ''}
      </td>`;
    tbody.appendChild(row);
  });
  tbody.querySelectorAll('button[data-id]').forEach(btn => {
    btn.addEventListener('click', () => respondTreaty(btn.dataset.id, btn.dataset.action));
  });
}

export async function proposeTreaty() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  const type = document.getElementById('treaty-type').value;
  const partnerId = document.getElementById('partner-alliance-id').value;
  const notes = document.getElementById('treaty-notes').value;
  const endDate = document.getElementById('treaty-end').value;
  await fetch('/api/diplomacy/propose_treaty', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User-ID': session.user.id },
    body: JSON.stringify({ treaty_type: type, partner_alliance_id: partnerId, notes, end_date: endDate })
  });
}

window.proposeTreaty = proposeTreaty;

async function respondTreaty(tid, action) {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  if (action === 'renew') {
    await fetch('/api/diplomacy/renew_treaty', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': session.user.id },
      body: JSON.stringify({ treaty_id: parseInt(tid, 10) })
    });
  } else {
    await fetch('/api/diplomacy/respond_treaty', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': session.user.id },
      body: JSON.stringify({ treaty_id: parseInt(tid, 10), response_action: action })
    });
  }
  loadTreaties(session.user.id);
}
