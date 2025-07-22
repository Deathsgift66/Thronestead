// Project Name: Thronestead©
// File Name: navigationCheck.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../../supabaseClient.js';

// Simple auth guard for pages that require a logged in user.
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const {
      data: { session }
    } = await supabase.auth.getSession();
    if (!session && !location.pathname.endsWith('login.html')) {
      window.location.href = 'login.html';
    }
  } catch (err) {
    console.error('❌ Navigation check failed:', err);
    if (!location.pathname.endsWith('login.html')) {
      window.location.href = 'login.html';
    }
  }
});

