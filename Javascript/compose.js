/*
Project Name: Kingmakers Rise Frontend
File Name: compose.js
Updated: 2025-06-13 by Codex
Purpose: Modular compose system supporting messages, announcements, treaties, and war declarations.
*/

import { supabase } from './supabaseClient.js';

let session = null;
let user = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: authData } = await supabase.auth.getSession();
  if (!authData?.session) return (window.location.href = 'login.html');
  session = authData.session;

  const userData = await supabase.auth.getUser();
  user = userData?.data?.user || null;

  setupTabs();
  bindFormHandlers();
  preloadDrafts();
});

// ===============================
// Tabs Setup
// ===============================
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

// ===============================
// Form Binding
// ===============================
function bindFormHandlers() {
  bindForm('message-form', submitMessage, ['msg-recipient', 'msg-content']);
  bindForm('notice-form', submitNotification, ['notice-title', 'notice-message']);
  bindForm('treaty-form', submitTreatyProposal, ['treaty-partner', 'treaty-type']);
  bindForm('war-form', submitWarDeclaration, ['war-defender', 'war-reason']);

  // Recipient Auto-Suggest
  const recipientInput = document.getElementById('msg-recipient');
  recipientInput?.addEventListener('input', () => loadRecipientSuggestions(recipientInput.value));

  // Previews
  const livePreviews = {
    'msg-content': 'msg-preview',
    'notice-message': 'notice-preview',
    'treaty-type': 'treaty-preview',
    'war-reason': 'war-preview'
  };

  Object.entries(livePreviews).forEach(([inputId, previewId]) => {
    const el = document.getElementById(inputId);
    el?.addEventListener('input', () => {
      const val = el.value || '';
      document.getElementById(previewId).textContent = val.length ? `${val.length} chars\n${val}` : '';
    });
  });
}

// Bind form + auto save draft
function bindForm(formId, handler, draftFields = []) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener('submit', handler);

  draftFields.forEach(fieldId => setupDraftPersistence(fieldId));
}

// ===============================
// Draft Persistence
// ===============================
function setupDraftPersistence(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const key = `compose-${id}`;
  el.value = localStorage.getItem(key) || '';
  el.addEventListener('input', () => localStorage.setItem(key, el.value));
}

function clearDraft(ids) {
  ids.forEach(id => localStorage.removeItem(`compose-${id}`));
}

// ===============================
// Suggestion Helpers
// ===============================
async function loadRecipientSuggestions(query) {
  const list = document.getElementById('recipient-list');
  if (!query) return (list.innerHTML = '');

  const { data, error } = await supabase
    .from('users')
    .select('user_id, username')
    .ilike('username', `${query}%`)
    .limit(5);

  if (error) {
    console.error('Recipient search failed', error);
    return;
  }

  list.innerHTML = '';
  (data || []).forEach(user => {
    const opt = document.createElement('option');
    opt.value = user.user_id;
    opt.textContent = user.username;
    list.appendChild(opt);
  });
}

// ===============================
// Submit Actions
// ===============================
export async function submitMessage(e) {
  e.preventDefault();
  const recipient_id = val('msg-recipient');
  const message = val('msg-content');
  const category = val('msg-category');
  if (!recipient_id || !message) return alert('Recipient and message required');

  const res = await send('/api/compose/send-message', { recipient_id, message, category });
  if (res) {
    alert('Message sent');
    clearDraft(['msg-recipient', 'msg-content']);
  }
}

export async function submitNotification(e) {
  e.preventDefault();
  const title = val('notice-title');
  const message = val('notice-message');
  const category = val('notice-category');
  const link_action = val('notice-link');
  if (!title || !message) return alert('Title and message required');

  const res = await send('/api/compose/send-notification', { title, message, category, link_action });
  if (res) alert('Notification sent');
}

export async function submitTreatyProposal(e) {
  e.preventDefault();
  const partner_alliance_id = val('treaty-partner');
  const treaty_type = val('treaty-type');
  if (!partner_alliance_id || !treaty_type) return alert('Partner and treaty type required');

  const res = await send('/api/compose/propose-treaty', { partner_alliance_id, treaty_type });
  if (res) alert('Treaty proposal sent');
}

export async function submitWarDeclaration(e) {
  e.preventDefault();
  const defender_id = val('war-defender');
  const war_reason = val('war-reason');
  if (!defender_id || !war_reason) return alert('Defender and reason required');

  const res = await send('/api/compose/declare-war', { defender_id, war_reason });
  if (res) alert('War declaration sent');
}

// ===============================
// Utility
// ===============================
function val(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : '';
}

async function send(endpoint, payload) {
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return true;
  } catch (err) {
    console.error(`❌ ${endpoint}:`, err);
    alert('Request failed.');
    return false;
  }
}
