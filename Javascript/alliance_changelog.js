import { supabase } from './supabaseClient.js';

async function fetchChangelog() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  const res = await fetch('/api/alliance/changelog', {
    headers: { 'X-User-ID': session.user.id }
  });
  const data = await res.json();
  const container = document.getElementById('changelog-list');
  container.innerHTML = '';
  data.forEach(entry => {
    const li = document.createElement('li');
    li.classList.add('log-entry');
    li.innerHTML = `
      <div class="log-time">${new Date(entry.timestamp).toLocaleString()}</div>
      <div class="log-type">${entry.event_type}</div>
      <div class="log-description">${entry.description}</div>
    `;
    container.appendChild(li);
  });
}

function applyFilters() {
  // Client-side filtering placeholder
}

window.addEventListener('DOMContentLoaded', fetchChangelog);
