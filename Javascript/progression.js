/*
Project Name: Kingmakers Rise Frontend
File Name: progression.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Castle and Nobility Progression API Helpers

// =========================
// API CALL FUNCTIONS
// =========================
export async function getCastleProgression() {
  const res = await fetch('/api/progression/castle');
  if (!res.ok) {
    throw new Error('Failed to fetch castle progression');
  }
  return res.json();
}

export async function upgradeCastle() {
  const res = await fetch('/api/progression/castle/upgrade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Failed to upgrade castle');
  }
  return res.json();
}

export async function viewNobles() {
  const res = await fetch('/api/progression/nobles');
  if (!res.ok) {
    throw new Error('Failed to fetch nobles');
  }
  return res.json();
}

export async function viewKnights() {
  const res = await fetch('/api/progression/knights');
  if (!res.ok) {
    throw new Error('Failed to fetch knights');
  }
  return res.json();
}

// =========================
// OPTIONAL DOM INTEGRATION
// =========================
document.addEventListener('DOMContentLoaded', async () => {
  // Castle Progression
  const castleEl = document.getElementById('castle-progress');
  if (castleEl) {
    try {
      const data = await getCastleProgression();
      castleEl.innerHTML = `
        <p><strong>Level:</strong> ${data.level}</p>
        <p><strong>XP:</strong> ${data.experience} / ${data.next_level_xp}</p>
      `;
    } catch (err) {
      console.error('❌', err);
      castleEl.innerHTML = '<p>Failed to load castle data.</p>';
    }
  }

  // Nobles
  const noblesEl = document.getElementById('noble-list');
  if (noblesEl) {
    try {
      const data = await viewNobles();
      noblesEl.innerHTML = '';
      const nobles = data.nobles || [];
      if (nobles.length === 0) {
        noblesEl.innerHTML = '<li>No nobles found.</li>';
      } else {
        nobles.forEach(n => {
          const li = document.createElement('li');
          li.textContent = n.name;
          noblesEl.appendChild(li);
        });
      }
    } catch (err) {
      console.error('❌', err);
      noblesEl.innerHTML = '<li>Failed to load nobles.</li>';
    }
  }

  // Knights
  const knightsEl = document.getElementById('knight-list');
  if (knightsEl) {
    try {
      const data = await viewKnights();
      knightsEl.innerHTML = '';
      const knights = data.knights || [];
      if (knights.length === 0) {
        knightsEl.innerHTML = '<li>No knights found.</li>';
      } else {
        knights.forEach(k => {
          const li = document.createElement('li');
          li.textContent = k.name;
          knightsEl.appendChild(li);
        });
      }
    } catch (err) {
      console.error('❌', err);
      knightsEl.innerHTML = '<li>Failed to load knights.</li>';
    }
  }

  // Upgrade Castle Button
  const upgradeBtn = document.getElementById('upgrade-castle-btn');
  if (upgradeBtn) {
    upgradeBtn.addEventListener('click', async () => {
      upgradeBtn.disabled = true;
      try {
        const result = await upgradeCastle();
        alert(result.message || 'Castle upgraded!');
        if (castleEl) {
          const data = await getCastleProgression();
          castleEl.innerHTML = `
            <p><strong>Level:</strong> ${data.level}</p>
            <p><strong>XP:</strong> ${data.experience} / ${data.next_level_xp}</p>
          `;
        }
      } catch (err) {
        console.error('❌', err);
        alert('Failed to upgrade castle.');
      } finally {
        upgradeBtn.disabled = false;
      }
    });
  }
});

