// Project Name: Thronestead©
// File Name: progressionGlobal.js
// Version 6.19.2025.22.06
// Developer: Codex
// ✅ Fetch progression summary from backend API and store globally + in sessionStorage
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
import { authHeaders } from './auth.js';

export async function fetchAndStorePlayerProgression(userId) {
  try {
    const headers = await authHeaders();
    headers['X-User-ID'] = userId;
    const res = await fetch(`${API_BASE_URL}/api/progression/summary`, {
      headers
    });

    if (res.status === 404) {
      const defaults = {
        castleLevel: 1,
        maxVillages: 1,
        availableNobles: 0,
        totalNobles: 0,
        availableKnights: 0,
        totalKnights: 0,
        troopSlots: { used: 0, available: 0 }
      };
      window.playerProgression = defaults;
      sessionStorage.setItem('playerProgression', JSON.stringify(defaults));
      return;
    }

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to fetch progression');

    const structured = {
      castleLevel: data.castle_level || 1,
      maxVillages: data.max_villages || 1,
      availableNobles: data.nobles_available || 0,
      totalNobles: data.nobles_total || 0,
      availableKnights: data.knights_available || 0,
      totalKnights: data.knights_total || 0,
      troopSlots: data.troop_slots || { used: 0, available: 0 }
    };

    window.playerProgression = structured;
    sessionStorage.setItem('playerProgression', JSON.stringify(structured));
  } catch (err) {
    console.error('❌ Failed to load player progression:', err);
    window.playerProgression = null;
    sessionStorage.removeItem('playerProgression');
  }
}

// ✅ Load from sessionStorage into global state
export function loadPlayerProgressionFromStorage() {
  const stored = sessionStorage.getItem('playerProgression');
  if (!stored) return;

  try {
    const parsed = JSON.parse(stored);
    if (typeof parsed === 'object' && parsed.castleLevel) {
      window.playerProgression = parsed;
    } else {
      throw new Error('Invalid structure');
    }
  } catch (err) {
    console.error('❌ Failed to parse stored progression:', err);
    window.playerProgression = null;
    sessionStorage.removeItem('playerProgression');
  }
}
