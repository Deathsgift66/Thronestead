// Project Name: Thronestead©
// File Name: kingdom_name_linkify.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Utility to linkify kingdom names in text content.
'use strict';

let kingdomMap = null;

async function loadKingdomMap() {
  if (kingdomMap) return kingdomMap;
  const cached = sessionStorage.getItem('kingdomMap');
  if (cached) {
    kingdomMap = JSON.parse(cached);
    return kingdomMap;
  }
  try {
    const res = await fetch('/api/kingdom/lookup');
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    kingdomMap = {};
    for (const row of data) {
      const id = row.kingdom_id ?? row.id;
      const name = row.kingdom_name ?? row.name;
      kingdomMap[name.toLowerCase()] = id;
    }
    sessionStorage.setItem('kingdomMap', JSON.stringify(kingdomMap));
  } catch (err) {
    console.error('Failed to load kingdom lookup', err);
    kingdomMap = {};
  }
  return kingdomMap;
}

function linkifyKingdoms(text) {
  if (!kingdomMap) return text;
  const pattern = /\b([A-Z][A-Za-z'\-]*(?:\s+[A-Z][A-Za-z'\-]*)*)\b/g;
  return text.replace(pattern, (m) => {
    const id = kingdomMap[m.toLowerCase()];
    if (id) {
      return `<a href="/kingdom_profile.html?kingdom_id=${id}" target="_blank" rel="noopener noreferrer">${m}</a>`;
    }
    return m;
  });
}

export async function applyKingdomLinks(containerSelector = '.message-content, .log-entry, .notification-body') {
  if (!kingdomMap) await loadKingdomMap();
  document.querySelectorAll(containerSelector).forEach((el) => {
    const original = el.textContent;
    const html = linkifyKingdoms(original);
    if (html !== original) {
      el.innerHTML = html;
    }
  });
}
