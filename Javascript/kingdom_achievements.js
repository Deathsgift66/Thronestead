import { supabase } from './supabaseClient.js';

let currentUser = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  currentUser = session.user;

  const { data: userRow, error: userError } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', currentUser.id)
    .single();
  if (userError) {
    console.error('❌ Failed to load user kingdom:', userError);
    return;
  }

  loadAchievements(userRow.kingdom_id);
});

async function loadAchievements(kingdomId) {
  const list = document.getElementById('kingdom-achievements-list');
  if (list) list.innerHTML = '<li>Loading achievements...</li>';

  try {
    const [catalogueRes, unlockedRes] = await Promise.all([
      supabase.from('kingdom_achievement_catalogue').select('*'),
      supabase
        .from('kingdom_achievements')
        .select('achievement_code, awarded_at')
        .eq('kingdom_id', kingdomId)
    ]);

    if (catalogueRes.error) throw catalogueRes.error;
    if (unlockedRes.error) throw unlockedRes.error;

    const unlockedMap = new Map(
      (unlockedRes.data || []).map(r => [r.achievement_code, r.awarded_at])
    );

    list.innerHTML = '';
    catalogueRes.data.forEach(row => {
      if (row.is_hidden && !unlockedMap.has(row.achievement_code)) {
        return;
      }
      const li = document.createElement('li');
      if (unlockedMap.has(row.achievement_code)) {
        li.innerHTML = `<strong>${escapeHTML(row.name)}</strong> - ${escapeHTML(row.description)} (${new Date(unlockedMap.get(row.achievement_code)).toLocaleDateString()})`;
      } else {
        li.textContent = row.name;
        li.classList.add('locked');
      }
      list.appendChild(li);
    });
  } catch (err) {
    console.error('❌ Failed to load achievements:', err);
    if (list) list.innerHTML = '<li>Failed to load achievements.</li>';
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
