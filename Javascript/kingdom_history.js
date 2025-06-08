/*
Project Name: Kingmakers Rise Frontend
File Name: kingdom_history.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  await loadHistory();
});

async function loadHistory() {
  const listEl = document.getElementById('history-list');
  listEl.innerHTML = '<li>Loading history...</li>';

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const res = await fetch(`/api/kingdom-history?kingdom_id=${userData.kingdom_id}&limit=50`);
    const result = await res.json();

    listEl.innerHTML = '';

    if (!result.history || result.history.length === 0) {
      listEl.innerHTML = '<li>No history found.</li>';
      return;
    }

    result.history.forEach(entry => {
      const item = document.createElement('li');
      item.classList.add('history-item');
      item.innerHTML = `
        <div class="date">[${new Date(entry.event_date).toLocaleString()}]</div>
        <div class="detail">${escapeHTML(entry.event_details)}</div>
      `;
      listEl.appendChild(item);
    });
  } catch (err) {
    console.error('Error loading history:', err);
    listEl.innerHTML = '<li>Failed to load history.</li>';
  }
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
