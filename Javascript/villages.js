import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  await loadVillages();
});

async function loadVillages() {
  const listEl = document.getElementById('village-list');
  listEl.innerHTML = '<li>Loading villages...</li>';

  try {
    const { data: { user } } = await supabase.auth.getUser();

    const { data: profile, error: profileError } = await supabase
      .from('users')
      .select('kingdom_id')
      .eq('user_id', user.id)
      .single();

    if (profileError) throw profileError;

    const { data: villages, error } = await supabase
      .from('villages')
      .select('village_id, village_name, population')
      .eq('kingdom_id', profile.kingdom_id)
      .order('village_name', { ascending: true });

    if (error) throw error;

    listEl.innerHTML = '';

    if (!villages || villages.length === 0) {
      listEl.innerHTML = '<li>No villages found.</li>';
      return;
    }

    villages.forEach(village => {
      const li = document.createElement('li');
      li.innerHTML = `
        <a href="village.html?village_id=${village.village_id}">${escapeHTML(village.village_name)}</a>
        <span>Pop: ${village.population.toLocaleString()}</span>
      `;
      listEl.appendChild(li);
    });
  } catch (err) {
    console.error('❌ Error loading villages:', err);
    listEl.innerHTML = '<li>Failed to load villages.</li>';
  }
}

function escapeHTML(str) {
  return str?.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
