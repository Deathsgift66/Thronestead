// Project Name: Thronestead©
// File Name: progression.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
//
// ─── API UTILITIES ───────────────────────────────────────────────────────────────
//

async function apiGET(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`GET failed: ${url}`);
  return res.json();
}

async function apiPOST(url, data = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || `POST failed: ${url}`);
  return json;
}

async function apiPUT(url, data = {}) {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || `PUT failed: ${url}`);
  return json;
}

async function apiDELETE(url, data = {}) {
  const res = await fetch(url, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || `DELETE failed: ${url}`);
  return json;
}

//
// ─── CASTLE PROGRESSION ───────────────────────────────────────────────────────────
//

export async function getCastleProgression() {
  return apiGET('https://thronestead.onrender.com/api/progression/castle');
}

export async function upgradeCastle() {
  return apiPOST('https://thronestead.onrender.com/api/progression/castle/upgrade');
}

//
// ─── NOBILITY ─────────────────────────────────────────────────────────────────────
//

export async function viewNobles() {
  return apiGET('https://thronestead.onrender.com/api/progression/nobles');
}

export async function nameNoble(name) {
  return apiPOST('https://thronestead.onrender.com/api/progression/nobles', { noble_name: name });
}

export async function renameNoble(oldName, newName) {
  return apiPUT('https://thronestead.onrender.com/api/progression/nobles/rename', {
    old_name: oldName,
    new_name: newName
  });
}

export async function removeNoble(name) {
  return apiDELETE('https://thronestead.onrender.com/api/progression/nobles', { noble_name: name });
}

//
// ─── KNIGHTHOOD ───────────────────────────────────────────────────────────────────
//

export async function viewKnights() {
  return apiGET('https://thronestead.onrender.com/api/progression/knights');
}

export async function nameKnight(name) {
  return apiPOST('https://thronestead.onrender.com/api/progression/knights', { knight_name: name });
}

export async function renameKnight(oldName, newName) {
  return apiPUT('https://thronestead.onrender.com/api/progression/knights/rename', {
    old_name: oldName,
    new_name: newName
  });
}

export async function removeKnight(name) {
  return apiDELETE('https://thronestead.onrender.com/api/progression/knights', { knight_name: name });
}

export async function promoteKnightApi(name) {
  return apiPOST('https://thronestead.onrender.com/api/progression/knights/promote', { knight_name: name });
}

//
// ─── DOM BINDINGS ────────────────────────────────────────────────────────────────
//

document.addEventListener('DOMContentLoaded', async () => {
  const castleEl = document.getElementById('castle-progress');
  if (castleEl) {
    try {
      const data = await getCastleProgression();
      castleEl.innerHTML = `
        <p><strong>Level:</strong> ${data.level}</p>
      `;
    } catch (err) {
      console.error('❌', err);
      castleEl.innerHTML = '<p>Failed to load castle progression.</p>';
    }
  }

  await renderNobles();
  await renderKnights();

  const nobleForm = document.getElementById('noble-form');
  nobleForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('new-noble-name').value.trim();
    if (!name) return;
    try {
      await nameNoble(name);
      nobleForm.reset();
      await renderNobles();
    } catch (err) {
      alert(err.message);
    }
  });

  const knightForm = document.getElementById('knight-form');
  knightForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('new-knight-name').value.trim();
    if (!name) return;
    try {
      await nameKnight(name);
      knightForm.reset();
      await renderKnights();
    } catch (err) {
      alert(err.message);
    }
  });

  const upgradeBtn = document.getElementById('upgrade-castle-btn');
  upgradeBtn?.addEventListener('click', async () => {
    upgradeBtn.disabled = true;
    try {
      const result = await upgradeCastle();
      alert(result.message || 'Castle upgraded!');
      const data = await getCastleProgression();
      castleEl.innerHTML = `
        <p><strong>Level:</strong> ${data.level}</p>
      `;
    } catch (err) {
      alert(err.message || 'Upgrade failed');
    } finally {
      upgradeBtn.disabled = false;
    }
  });
});

//
// ─── UI RENDER HELPERS ─────────────────────────────────────────────────────────────
//

async function renderNobles() {
  const el = document.getElementById('noble-list');
  if (!el) return;
  try {
    const { nobles = [] } = await viewNobles();
    el.innerHTML = nobles.length
      ? nobles.map(n => renderNameItem(n.name || n, 'noble')).join('')
      : '<li>No nobles found.</li>';
    bindNobleEvents();
  } catch (err) {
    console.error('❌', err);
    el.innerHTML = '<li>Failed to load nobles.</li>';
  }
}

async function renderKnights() {
  const el = document.getElementById('knight-list');
  if (!el) return;
  try {
    const { knights = [] } = await viewKnights();
    el.innerHTML = knights.length
      ? knights.map(k => renderNameItem(k.name || k, 'knight')).join('')
      : '<li>No knights found.</li>';
    bindKnightEvents();
  } catch (err) {
    console.error('❌', err);
    el.innerHTML = '<li>Failed to load knights.</li>';
  }
}

function renderNameItem(name, type) {
  const base = `<li><strong>${name}</strong>`;
  const buttons = {
    noble: `
      <button class="action-btn rename-noble" data-name="${name}">Rename</button>
      <button class="action-btn remove-noble" data-name="${name}">Remove</button>
    `,
    knight: `
      <button class="action-btn promote-knight" data-name="${name}">Promote</button>
      <button class="action-btn rename-knight" data-name="${name}">Rename</button>
      <button class="action-btn remove-knight" data-name="${name}">Remove</button>
    `
  };
  return `${base} ${buttons[type]}</li>`;
}

function bindNobleEvents() {
  document.querySelectorAll('.rename-noble').forEach(btn =>
    btn.addEventListener('click', async () => {
      const oldName = btn.dataset.name;
      const newName = prompt('Rename noble:', oldName);
      if (!newName) return;
      await renameNoble(oldName, newName);
      await renderNobles();
    })
  );
  document.querySelectorAll('.remove-noble').forEach(btn =>
    btn.addEventListener('click', async () => {
      const name = btn.dataset.name;
      if (confirm(`Remove noble ${name}?`)) {
        await removeNoble(name);
        await renderNobles();
      }
    })
  );
}

function bindKnightEvents() {
  document.querySelectorAll('.promote-knight').forEach(btn =>
    btn.addEventListener('click', async () => {
      await promoteKnightApi(btn.dataset.name);
      await renderKnights();
    })
  );
  document.querySelectorAll('.rename-knight').forEach(btn =>
    btn.addEventListener('click', async () => {
      const oldName = btn.dataset.name;
      const newName = prompt('Rename knight:', oldName);
      if (!newName) return;
      await renameKnight(oldName, newName);
      await renderKnights();
    })
  );
  document.querySelectorAll('.remove-knight').forEach(btn =>
    btn.addEventListener('click', async () => {
      const name = btn.dataset.name;
      if (confirm(`Remove knight ${name}?`)) {
        await removeKnight(name);
        await renderKnights();
      }
    })
  );
}
