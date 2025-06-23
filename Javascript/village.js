// Project Name: Thronestead©
// File Name: village.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  await loadVillagePage();
  const urlParams = new URLSearchParams(window.location.search);
  const villageId = urlParams.get('village_id');
  if (villageId) {
    initRealtime(villageId);
  }
});

async function loadVillagePage() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const villageId = urlParams.get('village_id');
    if (!villageId) {
      showToast('Invalid village ID.');
      return;
    }

    const res = await fetch(`/api/kingdom/villages/summary/${villageId}`);
    if (!res.ok) throw new Error('Failed to load village summary');
    const summary = await res.json();
    const village = summary.village;

    document.getElementById('village-name').textContent = village.village_name;

    await loadVillageResources(villageId);
    await loadVillageBuildings(villageId);
    await loadVillageModifiers(villageId);
    await loadVillageMilitary(villageId);
    await loadVillageQueue(villageId);
    await loadVillageEvents(villageId);

    showToast('Village loaded!');
  } catch (err) {
    console.error('❌ Error loading village:', err);
    showToast('Failed to load village.');
  }
}

async function loadVillageResources(villageId) {
  const gridEl = document.getElementById('resource-grid');
  gridEl.innerHTML = '<p>Loading resources...</p>';

  const { data: resData, error } = await supabase
    .from('village_resources')
    .select('*')
    .eq('village_id', villageId)
    .single();

  if (error) {
    console.error('❌ Error loading resources:', error);
    gridEl.innerHTML = '<p>Failed to load resources.</p>';
    return;
  }

  gridEl.innerHTML = '';

  Object.keys(resData).forEach(key => {
    if (key === 'village_id') return;
    const card = document.createElement('div');
    card.classList.add('resource-card');
    card.innerHTML = `
      <h4>${formatResourceName(key)}</h4>
      <p>${resData[key].toLocaleString()}</p>
    `;
    gridEl.appendChild(card);
  });
}

async function loadVillageBuildings(villageId) {
  const listEl = document.getElementById('building-list');
  listEl.innerHTML = '<p>Loading buildings...</p>';

  const { data: buildings, error } = await supabase
    .from('village_buildings')
    .select('building_name, level')
    .eq('village_id', villageId)
    .order('building_name', { ascending: true });

  if (error) {
    console.error('❌ Error loading buildings:', error);
    listEl.innerHTML = '<p>Failed to load buildings.</p>';
    return;
  }

  listEl.innerHTML = '';

  if (buildings.length === 0) {
    listEl.innerHTML = '<p>No buildings constructed.</p>';
    return;
  }

  buildings.forEach(building => {
    const card = document.createElement('div');
    card.classList.add('building-card');
    card.innerHTML = `
      <h4>${building.building_name}</h4>
      <p>Level: ${building.level}</p>
    `;
    listEl.appendChild(card);
  });
}

async function loadVillageModifiers(villageId) {
  const modEl = document.getElementById('modifier-list');
  if (!modEl) return;
  modEl.innerHTML = '<p>Loading modifiers...</p>';

  const { data: mods, error } = await supabase
    .from('village_modifiers')
    .select('*')
    .eq('village_id', villageId);

  if (error) {
    console.error('❌ Error loading modifiers:', error);
    modEl.innerHTML = '<p>Failed to load modifiers.</p>';
    return;
  }

  modEl.innerHTML = '';
  const now = Date.now();
  if (!mods || mods.length === 0) {
    modEl.innerHTML = '<p>No active modifiers.</p>';
    return;
  }

  mods.forEach(mod => {
    if (mod.expires_at && new Date(mod.expires_at).getTime() < now) return;
    const card = document.createElement('div');
    card.classList.add('modifier-card');
    card.innerHTML = `
      <h4>${mod.source}</h4>
      <p>Expires: ${mod.expires_at ? new Date(mod.expires_at).toLocaleDateString() : 'Never'}</p>
    `;
    modEl.appendChild(card);
  });
}

async function loadVillageMilitary(villageId) {
  const milEl = document.getElementById('military-stats');
  milEl.innerHTML = '<p>Loading military...</p>';

  const { data: military, error } = await supabase
    .from('village_military')
    .select('unit_name, quantity')
    .eq('village_id', villageId)
    .order('unit_name', { ascending: true });

  if (error) {
    console.error('❌ Error loading military:', error);
    milEl.innerHTML = '<p>Failed to load military.</p>';
    return;
  }

  milEl.innerHTML = '';

  if (military.length === 0) {
    milEl.innerHTML = '<p>No stationed troops.</p>';
    return;
  }

  military.forEach(unit => {
    const card = document.createElement('div');
    card.classList.add('military-card');
    card.innerHTML = `
      <h4>${unit.unit_name}</h4>
      <p>Quantity: ${unit.quantity}</p>
    `;
    milEl.appendChild(card);
  });
}

async function loadVillageQueue(villageId) {
  const queueEl = document.getElementById('queue-list');
  queueEl.innerHTML = '<p>Loading queue...</p>';

  const { data: queue, error } = await supabase
    .from('village_queue')
    .select('*')
    .eq('village_id', villageId)
    .order('queue_ends_at', { ascending: true });

  if (error) {
    console.error('❌ Error loading queue:', error);
    queueEl.innerHTML = '<p>Failed to load queue.</p>';
    return;
  }

  queueEl.innerHTML = '';

  if (queue.length === 0) {
    queueEl.innerHTML = '<p>No active build or training queue.</p>';
    return;
  }

  queue.forEach(entry => {
    const card = document.createElement('div');
    card.classList.add('queue-card');
    card.innerHTML = `
      <h4>${entry.queue_type}: ${entry.item_name}</h4>
      <p>Ends: ${new Date(entry.queue_ends_at).toLocaleString()}</p>
    `;
    queueEl.appendChild(card);
  });
}

async function loadVillageEvents(villageId) {
  const logEl = document.getElementById('event-log');
  logEl.innerHTML = '<p>Loading events...</p>';

  const { data: events, error } = await supabase
    .from('village_events')
    .select('*')
    .eq('village_id', villageId)
    .order('event_time', { descending: true })
    .limit(10);

  if (error) {
    console.error('❌ Error loading event log:', error);
    logEl.innerHTML = '<p>Failed to load event log.</p>';
    return;
  }

  logEl.innerHTML = '';

  if (events.length === 0) {
    logEl.innerHTML = '<p>No recent events.</p>';
    return;
  }

  events.forEach(event => {
    const entry = document.createElement('div');
    entry.classList.add('event-entry');
    entry.innerHTML = `
      <p>[${new Date(event.event_time).toLocaleString()}] ${event.event_description}</p>
    `;
    logEl.appendChild(entry);
  });
}

function initRealtime(villageId) {
  const indicator = document.getElementById('realtime-indicator');
  indicator.textContent = 'Connecting...';

  const reloadMap = {
    village_resources: loadVillageResources,
    village_events: loadVillageEvents,
    village_modifiers: loadVillageModifiers,
    village_buildings: loadVillageBuildings,
    village_military: loadVillageMilitary,
    village_queue: loadVillageQueue
  };

  const channel = supabase.channel('village_live_' + villageId);

  Object.entries(reloadMap).forEach(([table, fn]) => {
    channel.on('postgres_changes', {
      event: '*',
      schema: 'public',
      table,
      filter: `village_id=eq.${villageId}`
    }, () => fn(villageId));
  });

  channel.subscribe(status => {
    if (status === 'SUBSCRIBED') {
      indicator.textContent = 'Live';
      indicator.className = 'connected';
    } else {
      indicator.textContent = 'Offline';
      indicator.className = 'disconnected';
    }
  });

  window.addEventListener('beforeunload', () => {
    supabase.removeChannel(channel);
  });

  return channel;
}

function formatResourceName(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

function showToast(msg) {
  let toastEl = document.getElementById('toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.id = 'toast';
    toastEl.className = 'toast-notification';
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  setTimeout(() => {
    toastEl.classList.remove('show');
  }, 3000);
}
