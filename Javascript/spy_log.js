// Project Name: Thronestead©
// File Name: spy_log.js
// Version 6.14.2025.20.12
// Developer: Codex
import { supabase } from '../supabaseClient.js';
import { escapeHTML, showToast } from './utils.js';
import { applyKingdomLinks } from './kingdom_name_linkify.js';

let realtimeChannel = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  await loadSpyLog();
  subscribeRealtime();
  applyKingdomLinks();
});

async function loadSpyLog() {
  const body = document.getElementById('spy-log-body');
  if (!body) return;
  body.innerHTML = `<tr><td colspan="7">Loading...</td></tr>`;
  try {
    const res = await fetch('/api/spy/log');
    if (!res.ok) throw new Error('Failed to fetch log');
    const data = await res.json();
    body.innerHTML = '';
    const logs = data.logs || [];
    if (!logs.length) {
      body.innerHTML = `<tr><td colspan="7">No missions found.</td></tr>`;
      return;
    }
    logs.forEach(entry => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${escapeHTML(entry.mission_type || '')}</td>
        <td>${escapeHTML(entry.target_name || entry.target_id || '')}</td>
        <td>${entry.outcome === 'success' ? '✅' : '❌'}</td>
        <td>${entry.accuracy != null ? entry.accuracy + '%' : '-'}</td>
        <td>${entry.detected ? '⚠️' : ''}</td>
        <td>${entry.spies_lost || 0}</td>
        <td>${formatDate(entry.timestamp)}</td>
      `;
      body.appendChild(row);
    });
    applyKingdomLinks();
  } catch (err) {
    console.error('spy log load error:', err);
    body.innerHTML = `<tr><td colspan="7">Failed to load log.</td></tr>`;
    showToast('Failed to load spy log.');
  }
}

function subscribeRealtime() {
  realtimeChannel = supabase
    .channel('public:spy_missions')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'spy_missions' }, loadSpyLog)
    .subscribe(status => {
      const indicator = document.getElementById('realtime-indicator');
      if (indicator) {
        indicator.textContent = status === 'SUBSCRIBED' ? 'Live' : 'Offline';
        indicator.className = status === 'SUBSCRIBED' ? 'connected' : 'disconnected';
      }
    });

  window.addEventListener('beforeunload', () => {
    if (realtimeChannel) supabase.removeChannel(realtimeChannel);
  });
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString();
}
