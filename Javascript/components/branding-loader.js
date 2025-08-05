// Project Name: Thronestead©
// File Name: brandingLoader.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66

// Injects shared alliance branding visuals into pages

document.addEventListener('DOMContentLoaded', () => {
  const targets = document.querySelectorAll('.alliance-branding');
  if (!targets.length) return;

  // Resolve to /public/alliance_branding.html regardless of nesting
  const BRANDING_PATH = new URL('../../public/alliance_branding.html', import.meta.url).pathname;

  fetch(BRANDING_PATH)
    .then(res => res.text())
    .then(html => {
      targets.forEach(el => {
        el.innerHTML = html;
      });
    })
    .catch(err => {
      console.error('❌ Alliance branding injection failed:', err);
    });
});
