import { loadPlayerProgressionFromStorage } from './progressionGlobal.js';

// Inject a small banner showing key progression stats using window.playerProgression
export function renderProgressionBanner() {
  loadPlayerProgressionFromStorage();
  const prog = window.playerProgression;
  if (!prog) return;

  let bar = document.getElementById('progression-bar');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'progression-bar';
    bar.className = 'progression-bar';
    document.body.prepend(bar);
  }

  bar.innerHTML = `
    <span>Castle Lv ${prog.castleLevel}</span>
    <span>Villages ${prog.maxVillages}</span>
    <span>Nobles ${prog.availableNobles}/${prog.totalNobles}</span>
    <span>Knights ${prog.availableKnights}/${prog.totalKnights}</span>
    <span>Slots ${prog.troopSlots.used}/${prog.troopSlots.used + prog.troopSlots.available}</span>
  `;
}

document.addEventListener('DOMContentLoaded', renderProgressionBanner);
