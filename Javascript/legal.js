/*
Project Name: Kingmakers Rise Frontend
File Name: legal.js
Date: June 2, 2025
Author: Deathsgift66
Description: Dynamic legal page handling for Terms, Policies, DMCA, GDPR, etc.
*/

import { supabase } from './supabaseClient.js';

let docs = [];
let realtimeSub = null;

// ✅ On page ready, load and watch documents
document.addEventListener('DOMContentLoaded', async () => {
  await loadDocuments();
  setupRealtimeSync();

  const search = document.getElementById('doc-search');
  if (search) {
    search.addEventListener('input', filterDocuments);
  }
});

// ✅ Load document metadata from backend
async function loadDocuments() {
  const container = document.getElementById('legal-docs');
  container.innerHTML = '<p>Loading documents...</p>';
  try {
    const res = await fetch('/api/legal/documents');
    const data = await res.json();
    docs = data.documents || [];
    renderDocuments(docs);
  } catch (err) {
    console.error('❌ Failed to fetch legal documents:', err);
    container.innerHTML = '<p>Failed to load documents.</p>';
  }
}

// ✅ Realtime document update handler
function setupRealtimeSync() {
  realtimeSub = supabase
    .channel('legal_documents')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'legal_documents' }, async () => {
      await loadDocuments();
    })
    .subscribe();
}

// ✅ Clean up listener on exit
window.addEventListener('beforeunload', () => {
  realtimeSub?.unsubscribe();
});

// 🔍 Search documents by title
function filterDocuments() {
  const searchEl = document.getElementById('doc-search');
  const query = searchEl?.value.toLowerCase() || '';
  const filtered = docs.filter(doc => doc.title.toLowerCase().includes(query));
  renderDocuments(filtered);
}

// 🧾 Render document cards
function renderDocuments(list) {
  const container = document.getElementById('legal-docs');
  container.innerHTML = '';

  if (!list.length) {
    container.innerHTML = '<p>No documents found.</p>';
    return;
  }

  list.forEach(doc => {
    const card = document.createElement('div');
    card.className = 'legal-card';
    card.innerHTML = `
      <h3>${escapeHTML(doc.title)}</h3>
      <p>${escapeHTML(doc.summary)}</p>
      <a href="${escapeHTML(doc.url)}" target="_blank" rel="noopener noreferrer">View Document</a>
    `;
    container.appendChild(card);
  });
}

// 🧼 Escape HTML output to prevent XSS
function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
