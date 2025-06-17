// Project Name: Thronestead©
// File Name: village.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
function initRealtime(villageId) {
  const indicator = document.getElementById('realtime-indicator');
  indicator.textContent = 'Connecting...';

  const reloadMap = {
    'village_resources': loadVillageResources,
    'village_events': loadVillageEvents,
    'village_modifiers': loadVillageModifiers,
    'village_buildings': loadVillageBuildings,
    'village_military': loadVillageMilitary,
    'village_queue': loadVillageQueue
  };

  const channel = supabase.channel('village_live_' + villageId);

  Object.entries(reloadMap).forEach(([table, fn]) => {
    channel.on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: table,
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
