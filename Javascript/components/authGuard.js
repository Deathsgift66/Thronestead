// Project Name: Thronestead©
// File Name: authGuard.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../../supabaseClient.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';
import { startSessionRefresh } from '../auth.js';

// Configurable per page
const requireAdmin = window.requireAdmin === true;

(async () => {
  try {
    if (window.location.pathname === '/login.html') {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        return (window.location.href = '/overview.html');
      }
      return;
    }

    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      return (window.location.href = '/login.html');
    }

    let { data: { user }, error } = await supabase.auth.getUser();
    if (!user || error) {
      const { data: refreshed } = await supabase.auth.refreshSession();
      if (!refreshed?.user) {
        return (window.location.href = '/login.html');
      }
      user = refreshed.user;
    }

    startSessionRefresh();

    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();

    if (!userData || userErr) {
      return (window.location.href = '/login.html');
    }

    if (!userData.setup_complete) {
      return (window.location.href = '/play.html');
    }

    if (requireAdmin && userData.is_admin !== true) {
      return (window.location.href = '/overview.html');
    }

    window.user = { id: user.id, is_admin: userData.is_admin };

    loadPlayerProgressionFromStorage();
    if (!window.playerProgression) {
      await fetchAndStorePlayerProgression(user.id);
    }

  } catch (err) {
    console.error('authGuard failure:', err);
    window.location.href = '/login.html';
  }
})();
