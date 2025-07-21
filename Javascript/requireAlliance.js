// Project Name: Thronestead©
// File Name: requireAlliance.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { enforceAllianceOrAdminAccess } from './utils.js';

window.requireAlliance = true;

// Ensure the viewer is either an alliance member or an admin before
// other modules on the page execute. Redirects automatically when
// unauthorized.
document.addEventListener('DOMContentLoaded', () => {
  enforceAllianceOrAdminAccess().catch(err => {
    console.error('Alliance guard failed:', err);
  });
});
