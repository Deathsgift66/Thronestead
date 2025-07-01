// Comment
// Project Name: Thronestead©
// File Name: kingdom_name_linkify.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
// Utility to linkify kingdom names in text content.

let kingdomMap = null;

async function loadKingdomMap() {
  if (kingdomMap) return kingdomMap;
  try {
    const res = await fetch('/api/kingdom/lookup');
    const data = await res.json();
    kingdomMap = {};
    for (const row of data) {
      const id = row.kingdom_id ?? row.id;
      const name = row.kingdom_name ?? row.name;
      kingdomMap[name] = id;
    }
  } catch (err) {
    console.error('Failed to load kingdom lookup', err);
    kingdomMap = {};
  }
  return kingdomMap;
}

function linkifyKingdoms(text) {
  if (!kingdomMap) return text;
  const pattern = /\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)\b/g;
  return text.replace(pattern, (match) => {
    const id = kingdomMap[match];
    if (id) {
      return `<a href="/kingdom_profile.html?kingdom_id=${id}" target="_blank" rel="noopener noreferrer">${match}</a>`;
    }
    return match;
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
