// Project Name: Thronestead©
// File Name: requireAdmin.js
// Version: 7/21/2025
// Developer: Deathsgift66

'use strict';

window.requireAdmin = true;

// Ensure <meta name="require-admin" content="true"> exists for authGuard
const existing = document.querySelector('meta[name="require-admin"]');
if (!existing) {
  const meta = document.createElement('meta');
  meta.name = 'require-admin';
  meta.content = 'true';
  document.head.appendChild(meta);
} else {
  existing.content = 'true';
}
