import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  setupTabs();
  bindForms();
});

function setupTabs() {
  const tabs = document.querySelectorAll('.tab');
  const contents = document.querySelectorAll('.tab-content');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      contents.forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.tab).classList.add('active');
    });
  });
}

function bindForms() {
  document.getElementById('message-form').addEventListener('submit', submitMessage);
  document.getElementById('notice-form').addEventListener('submit', submitNotification);
  document.getElementById('treaty-form').addEventListener('submit', submitTreatyProposal);
  document.getElementById('war-form').addEventListener('submit', submitWarDeclaration);

  const recipientInput = document.getElementById('msg-recipient');
  recipientInput.addEventListener('input', () => loadRecipientSuggestions(recipientInput.value));
  if (recipientInput.value) loadRecipientSuggestions(recipientInput.value);

  // Draft saving
  ['msg-recipient','msg-content','notice-title','notice-message','notice-category','notice-link','treaty-partner','treaty-type','war-defender','war-reason']
    .forEach(id => setupDraft(id));

  // Live previews
  document.getElementById('msg-content').addEventListener('input', () => {
    const val = document.getElementById('msg-content').value;
    document.getElementById('msg-preview').textContent = `${val.length} chars\n${val}`;
  });
  document.getElementById('notice-message').addEventListener('input', () => {
    document.getElementById('notice-preview').textContent = document.getElementById('notice-message').value;
  });
  document.getElementById('treaty-type').addEventListener('input', () => {
    document.getElementById('treaty-preview').textContent = document.getElementById('treaty-type').value;
  });
  document.getElementById('war-reason').addEventListener('input', () => {
    document.getElementById('war-preview').textContent = document.getElementById('war-reason').value;
  });
}

function storageKey(id) { return `compose-${id}`; }
function setupDraft(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = localStorage.getItem(storageKey(id)) || '';
  el.addEventListener('input', () => {
    localStorage.setItem(storageKey(id), el.value);
  });
}

// Fetch recipient suggestions from Supabase
async function loadRecipientSuggestions(query) {
  if (!query) {
    document.getElementById('recipient-list').innerHTML = '';
    return;
  }
  const { data, error } = await supabase
    .from('users')
    .select('user_id, username')
    .ilike('username', `${query}%`)
    .limit(5);
  if (error) {
    console.error('Suggestion error', error);
    return;
  }
  const list = document.getElementById('recipient-list');
  list.innerHTML = '';
  (data || []).forEach(u => {
    const opt = document.createElement('option');
    opt.value = u.user_id;
    opt.textContent = u.username;
    list.appendChild(opt);
  });
}

export async function submitMessage(e) {
  e.preventDefault();
  const recipient_id = document.getElementById('msg-recipient').value.trim();
  const message = document.getElementById('msg-content').value.trim();
  const category = document.getElementById('msg-category').value;
  if (!recipient_id || !message) {
    alert('Recipient and message required');
    return;
  }
  try {
    const res = await fetch('/api/compose/send-message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient_id, message, category })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'failed');
    alert('Message sent');
    localStorage.removeItem(storageKey('msg-recipient'));
    localStorage.removeItem(storageKey('msg-content'));
  } catch (err) {
    console.error(err);
    alert('Failed to send message');
  }
}

export async function submitNotification(e) {
  e.preventDefault();
  const title = document.getElementById('notice-title').value.trim();
  const message = document.getElementById('notice-message').value.trim();
  const category = document.getElementById('notice-category').value.trim();
  const link_action = document.getElementById('notice-link').value.trim();
  if (!title || !message) {
    alert('Title and message required');
    return;
  }
  try {
    const res = await fetch('/api/compose/send-notification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, message, category, link_action })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'failed');
    alert('Notification sent');
  } catch (err) {
    console.error(err);
    alert('Failed to send notification');
  }
}

export async function submitTreatyProposal(e) {
  e.preventDefault();
  const partner_alliance_id = document.getElementById('treaty-partner').value.trim();
  const treaty_type = document.getElementById('treaty-type').value.trim();
  if (!partner_alliance_id || !treaty_type) {
    alert('Partner and treaty type required');
    return;
  }
  try {
    const res = await fetch('/api/compose/propose-treaty', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ partner_alliance_id, treaty_type })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'failed');
    alert('Treaty proposal sent');
  } catch (err) {
    console.error(err);
    alert('Failed to propose treaty');
  }
}

export async function submitWarDeclaration(e) {
  e.preventDefault();
  const defender_id = document.getElementById('war-defender').value.trim();
  const war_reason = document.getElementById('war-reason').value.trim();
  if (!defender_id || !war_reason) {
    alert('Defender and reason required');
    return;
  }
  try {
    const res = await fetch('/api/compose/declare-war', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ defender_id, war_reason })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'failed');
    alert('War declaration sent');
  } catch (err) {
    console.error(err);
    alert('Failed to declare war');
  }
}
