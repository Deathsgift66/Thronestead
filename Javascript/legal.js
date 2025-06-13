/*
Project Name: Kingmakers Rise Frontend
File Name: legal.js
Date: June 2, 2025
Author: Deathsgift66
*/
// legal.js - Handles loading and dynamic interactions for legal page

import { supabase } from './supabaseClient.js';

let docs = [];
let realtimeSub;

document.addEventListener('DOMContentLoaded', async () => {
  await loadDocuments();
  setupRealtime();

  const search = document.getElementById('doc-search');
  if (search) search.addEventListener('input', filterDocuments);
});

async function loadDocuments() {
  const container = document.getElementById('legal-docs');
  container.innerHTML = '<p>Loading documents...</p>';
  try {
    const res = await fetch('/api/legal/documents');
    const data = await res.json();
    docs = data.documents || [];
    renderDocuments(docs);
  } catch (err) {
    console.error('Error loading legal documents:', err);
    container.innerHTML = '<p>Failed to load documents.</p>';
  }
}

function setupRealtime() {
  realtimeSub = supabase
    .channel('legal_documents')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'legal_documents' }, async () => {
      await loadDocuments();
    })
    .subscribe();
}

window.addEventListener('beforeunload', () => {
  realtimeSub?.unsubscribe();
});

function filterDocuments() {
  const q = document.getElementById('doc-search').value.toLowerCase();
  const filtered = docs.filter(d => d.title.toLowerCase().includes(q));
  renderDocuments(filtered);
}

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
      <a href="${escapeHTML(doc.url)}" target="_blank">View Document</a>
    `;
    container.appendChild(card);
  });
}

function escapeHTML(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
