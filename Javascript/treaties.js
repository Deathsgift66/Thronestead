import { supabase } from './supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  await loadTreaties();
});

async function loadTreaties() {
  const container = document.getElementById('treaty-list');
  container.textContent = 'Loading...';
  try {
    const { data: { user } } = await supabase.auth.getUser();
    const res = await fetch('/api/kingdom/treaties', { headers: { 'X-User-ID': user.id } });
    const data = await res.json();
    container.innerHTML = '';
    (data.treaties || []).forEach(t => {
      const div = document.createElement('div');
      div.textContent = t.name;
      container.appendChild(div);
    });
  } catch (e) {
    container.textContent = 'Failed to load treaties';
  }
}
