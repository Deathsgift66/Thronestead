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

export async function nameNoble(nobleName) {
  const res = await fetch('/api/progression/nobles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ noble_name: nobleName })
  });
  if (!res.ok) throw new Error('Failed to name noble');
  return res.json();
}

export async function renameNoble(oldName, newName) {
  const res = await fetch('/api/progression/nobles/rename', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ old_name: oldName, new_name: newName })
  });
  if (!res.ok) throw new Error('Failed to rename noble');
  return res.json();
}

export async function removeNoble(nobleName) {
  const res = await fetch('/api/progression/nobles', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ noble_name: nobleName })
  });
  if (!res.ok) throw new Error('Failed to remove noble');
  return res.json();
}

export async function nameKnight(knightName) {
  const res = await fetch('/api/progression/knights', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ knight_name: knightName })
  });
  if (!res.ok) throw new Error('Failed to name knight');
  return res.json();
}

export async function renameKnight(oldName, newName) {
  const res = await fetch('/api/progression/knights/rename', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ old_name: oldName, new_name: newName })
  });
  if (!res.ok) throw new Error('Failed to rename knight');
  return res.json();
}

export async function promoteKnightApi(knightName) {
  const res = await fetch('/api/progression/knights/promote', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ knight_name: knightName })
  });
  if (!res.ok) throw new Error('Failed to promote knight');
  return res.json();
}

export async function removeKnight(knightName) {
  const res = await fetch('/api/progression/knights', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ knight_name: knightName })
  });
  if (!res.ok) throw new Error('Failed to remove knight');
  return res.json();
}

// =========================
// OPTIONAL DOM INTEGRATION
// =========================
document.addEventListener('DOMContentLoaded', async () => {
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

  await renderNobles();
  await renderKnights();

  const nobleForm = document.getElementById('noble-form');
  if (nobleForm) {
    nobleForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('new-noble-name').value.trim();
      if (!name) return;
      try {
        await nameNoble(name);
        nobleForm.reset();
        await renderNobles();
      } catch (err) {
        alert('Failed to name noble');
      }
    });
  }

  const knightForm = document.getElementById('knight-form');
  if (knightForm) {
    knightForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('new-knight-name').value.trim();
      if (!name) return;
      try {
        await nameKnight(name);
        knightForm.reset();
        await renderKnights();
      } catch (err) {
        alert('Failed to name knight');
      }
    });
  }

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

async function renderNobles() {
  const noblesEl = document.getElementById('noble-list');
  if (!noblesEl) return;
  try {
    const data = await viewNobles();
    noblesEl.innerHTML = '';
    const nobles = data.nobles || [];
    if (nobles.length === 0) {
      noblesEl.innerHTML = '<li>No nobles found.</li>';
    } else {
      nobles.forEach((n) => {
        const li = document.createElement('li');
        li.textContent = n.name || n;
        const renameBtn = document.createElement('button');
        renameBtn.textContent = 'Rename';
        renameBtn.className = 'action-btn';
        renameBtn.addEventListener('click', async () => {
          const newName = prompt('New name for noble:', n.name || n);
          if (!newName) return;
          try {
            await renameNoble(n.name || n, newName);
            await renderNobles();
          } catch {
            alert('Failed to rename noble');
          }
        });
        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Remove';
        removeBtn.className = 'action-btn';
        removeBtn.addEventListener('click', async () => {
          if (!confirm('Remove this noble?')) return;
          try {
            await removeNoble(n.name || n);
            await renderNobles();
          } catch {
            alert('Failed to remove noble');
          }
        });
        li.append(' ', renameBtn, ' ', removeBtn);
        noblesEl.appendChild(li);
      });
    }
  } catch (err) {
    console.error('❌', err);
    noblesEl.innerHTML = '<li>Failed to load nobles.</li>';
  }
}

async function renderKnights() {
  const knightsEl = document.getElementById('knight-list');
  if (!knightsEl) return;
  try {
    const data = await viewKnights();
    knightsEl.innerHTML = '';
    const knights = data.knights || [];
    if (knights.length === 0) {
      knightsEl.innerHTML = '<li>No knights found.</li>';
    } else {
      knights.forEach((k) => {
        const li = document.createElement('li');
        li.textContent = k.name || k;
        const promoteBtn = document.createElement('button');
        promoteBtn.textContent = 'Promote';
        promoteBtn.className = 'action-btn';
        promoteBtn.addEventListener('click', async () => {
          try {
            await promoteKnightApi(k.name || k);
            await renderKnights();
          } catch {
            alert('Failed to promote knight');
          }
        });
        const renameBtn = document.createElement('button');
        renameBtn.textContent = 'Rename';
        renameBtn.className = 'action-btn';
        renameBtn.addEventListener('click', async () => {
          const newName = prompt('New name for knight:', k.name || k);
          if (!newName) return;
          try {
            await renameKnight(k.name || k, newName);
            await renderKnights();
          } catch {
            alert('Failed to rename knight');
          }
        });
        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Remove';
        removeBtn.className = 'action-btn';
        removeBtn.addEventListener('click', async () => {
          if (!confirm('Remove this knight?')) return;
          try {
            await removeKnight(k.name || k);
            await renderKnights();
          } catch {
            alert('Failed to remove knight');
          }
        });
        li.append(' ', promoteBtn, ' ', renameBtn, ' ', removeBtn);
        knightsEl.appendChild(li);
      });
    }
  } catch (err) {
    console.error('❌', err);
    knightsEl.innerHTML = '<li>Failed to load knights.</li>';
  }
}

