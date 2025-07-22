// Project Name: Thronestead©
// File Name: progression.js
// Consolidated progression utilities and banner renderer
// Combines progressionGlobal.js and progressionBanner.js functionality

import { getEnvVar } from './env.js';
import { authFetch } from './utils.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');

export async function fetchAndStorePlayerProgression(userId) {
  try {
    const res = await authFetch(`${API_BASE_URL}/api/progression/summary`, {
      headers: { 'X-User-ID': userId }
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
    clearStoredProgression();
  }
}

export function clearStoredProgression() {
  window.playerProgression = null;
  try {
    sessionStorage.removeItem('playerProgression');
  } catch (e) {
    console.warn('⚠️ Failed to clear progression:', e);
  }
}

export function renderProgressionBanner(target = 'body') {
  loadPlayerProgressionFromStorage();
  const prog = window.playerProgression;
  if (!prog) return;

  let bar = document.getElementById('progression-bar');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'progression-bar';
    bar.className = 'progression-bar';

    const container = document.querySelector(target);
    if (container) container.prepend(bar);
  }

  bar.innerHTML = `
    <span><strong>🏰 Castle:</strong> Lv ${prog.castleLevel}</span>
    <span><strong>🏘️ Villages:</strong> ${prog.maxVillages}</span>
    <span><strong>👑 Nobles:</strong> ${prog.availableNobles}/${prog.totalNobles}</span>
    <span><strong>🛡️ Knights:</strong> ${prog.availableKnights}/${prog.totalKnights}</span>
    <span><strong>⚔️ Troops:</strong> ${prog.troopSlots.used}/${prog.troopSlots.used + prog.troopSlots.available}</span>
    ${prog.allianceLevel ? `<span><strong>🤝 Alliance:</strong> Lv ${prog.allianceLevel}</span>` : ''}
    ${prog.projectMilestones ? `<span><strong>🏗️ Milestones:</strong> ${prog.projectMilestones}</span>` : ''}
    ${prog.unlockRequirements ? `<span><strong>🔓 Unlocks:</strong> ${prog.unlockRequirements}</span>` : ''}
  `;
}

document.addEventListener('DOMContentLoaded', () => renderProgressionBanner());
