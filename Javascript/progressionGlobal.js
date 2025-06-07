/*
Project Name: Kingmakers Rise Frontend
File Name: progressionGlobal.js
Created: 2025-06-02
Author: Deathsgift66 (modified by Codex)
*/

// Utility to fetch player progression summary and store globally
export async function fetchAndStorePlayerProgression(userId) {
  try {
    const res = await fetch('/api/progression/summary', {
      headers: { 'X-User-ID': userId }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch progression');

    window.playerProgression = {
      castleLevel: data.castle_level,
      maxVillages: data.max_villages,
      availableNobles: data.nobles_available,
      totalNobles: data.nobles_total,
      availableKnights: data.knights_available,
      totalKnights: data.knights_total,
      troopSlots: data.troop_slots
    };
    sessionStorage.setItem('playerProgression', JSON.stringify(window.playerProgression));
  } catch (err) {
    console.error('Failed to load player progression', err);
  }
}

// Load progression from sessionStorage if available
export function loadPlayerProgressionFromStorage() {
  const stored = sessionStorage.getItem('playerProgression');
  if (stored) {
    try {
      window.playerProgression = JSON.parse(stored);
    } catch (err) {
      console.error('Failed to parse stored progression', err);
      sessionStorage.removeItem('playerProgression');
    }
  }
}
