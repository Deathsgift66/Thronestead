// Project Name: Kingmakers Rise©
// File Name: progressionBanner.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { loadPlayerProgressionFromStorage } from './progressionGlobal.js';

// ✅ Render the fixed banner using `window.playerProgression`
export function renderProgressionBanner(target = 'body') {
  loadPlayerProgressionFromStorage();
  const prog = window.playerProgression;
  if (!prog) return;

  let bar = document.getElementById('progression-bar');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'progression-bar';
    bar.className = 'progression-bar';

    // Safely prepend to specified target
    const container = document.querySelector(target);
    if (container) container.prepend(bar);
  }

  // ✅ Update content
  bar.innerHTML = `
    <span><strong>🏰 Castle:</strong> Lv ${prog.castleLevel}</span>
    <span><strong>🏘️ Villages:</strong> ${prog.maxVillages}</span>
    <span><strong>👑 Nobles:</strong> ${prog.availableNobles}/${prog.totalNobles}</span>
    <span><strong>🛡️ Knights:</strong> ${prog.availableKnights}/${prog.totalKnights}</span>
    <span><strong>⚔️ Troops:</strong> ${prog.troopSlots.used}/${prog.troopSlots.used + prog.troopSlots.available}</span>
  `;
}

// ✅ Auto-render on page load
document.addEventListener('DOMContentLoaded', () => renderProgressionBanner());
