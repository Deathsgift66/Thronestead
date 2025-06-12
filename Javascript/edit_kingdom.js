import { supabase } from './supabaseClient.js';

let userId = null;
let authToken = '';

async function loadRegions() {
  const sel = document.getElementById('region');
  const { data, error } = await supabase.from('region_catalogue').select('*');
  if (error) {
    sel.innerHTML = '<option value="">Failed to load</option>';
    return;
  }
  sel.innerHTML = '<option value="">Select Region</option>';
  data.forEach(r => {
    const opt = document.createElement('option');
    opt.value = r.region_code;
    opt.textContent = r.region_name || r.region_code;
    sel.appendChild(opt);
  });
}

async function loadKingdom() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  userId = session.user.id;
  authToken = session.access_token;
  const { data, error } = await supabase
    .from('kingdoms')
    .select('ruler_name,ruler_title,kingdom_name,motto,description,region,banner_url,emblem_url,is_on_vacation,kingdom_religion(religion_name)')
    .eq('owner_id', userId)
    .single();
  if (error || !data) {
    showToast('Failed to load kingdom');
    return;
  }
  document.getElementById('ruler_name').value = data.ruler_name || '';
  document.getElementById('ruler_title').value = data.ruler_title || '';
  document.getElementById('kingdom_name').value = data.kingdom_name || '';
  document.getElementById('motto').value = data.motto || '';
  document.getElementById('description').value = data.description || '';
  document.getElementById('region').value = data.region || '';
  document.getElementById('banner_url').value = data.banner_url || '';
  document.getElementById('emblem_url').value = data.emblem_url || '';
  document.getElementById('religion').value = data.kingdom_religion?.religion_name || '';
  if (data.banner_url) document.getElementById('banner-preview').src = data.banner_url;
  if (data.emblem_url) document.getElementById('emblem-preview').src = data.emblem_url;
  if (data.is_on_vacation) {
    document.getElementById('vacation-warning').classList.remove('hidden');
    document.querySelectorAll('#kingdom-form input, #kingdom-form textarea, #kingdom-form select, #kingdom-form button').forEach(el => {
      el.disabled = true;
    });
  }
}

function isValidURL(str) {
  try {
    new URL(str);
    return true;
  } catch {
    return false;
  }
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

document.addEventListener('DOMContentLoaded', async () => {
  await loadRegions();
  await loadKingdom();

  document.getElementById('banner_url').addEventListener('input', e => {
    document.getElementById('banner-preview').src = e.target.value;
  });
  document.getElementById('emblem_url').addEventListener('input', e => {
    document.getElementById('emblem-preview').src = e.target.value;
  });

  document.getElementById('kingdom-form').addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      ruler_name: document.getElementById('ruler_name').value.trim(),
      ruler_title: document.getElementById('ruler_title').value.trim(),
      kingdom_name: document.getElementById('kingdom_name').value.trim(),
      motto: document.getElementById('motto').value.trim() || null,
      description: document.getElementById('description').value.trim() || null,
      region: document.getElementById('region').value || null,
      banner_url: document.getElementById('banner_url').value.trim() || null,
      emblem_url: document.getElementById('emblem_url').value.trim() || null,
      religion_name: document.getElementById('religion').value.trim() || null
    };

    if (!payload.kingdom_name || !payload.ruler_name || !payload.ruler_title) {
      showToast('Name and title are required');
      return;
    }
    if (payload.banner_url && !isValidURL(payload.banner_url)) {
      showToast('Invalid banner URL');
      return;
    }
    if (payload.emblem_url && !isValidURL(payload.emblem_url)) {
      showToast('Invalid emblem URL');
      return;
    }

    const res = await fetch('/api/kingdom/update', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
        Authorization: `Bearer ${authToken}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      showToast('Failed to save changes');
      return;
    }
    showToast('Kingdom updated!');
  });
});
