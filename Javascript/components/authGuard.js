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
import { getEnvVar } from '../env.js';

// Configurable per page
const requireAdmin = window.requireAdmin === true;
// Pages that don't require authentication
const publicPages = ['/about.html', '/index.html', '/projects.html'];

(async () => {
  if (window.location.pathname === '/404.html') {
    console.info('Auth guard skipped on 404 page.');
    return;
  }
  try {
    if (window.location.pathname === '/login.html') {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        return (window.location.href = '/overview.html');
      }
      return;
    }

    if (publicPages.includes(window.location.pathname)) {
      return;
    }

    let { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      const { data } = await supabase.auth.refreshSession();
      session = data?.session;
    }
    if (!session?.access_token) {
      return (window.location.href = '/login.html');
    }

    const API_BASE_URL = getEnvVar('API_BASE_URL');
    try {
      const res = await fetch(`${API_BASE_URL}/api/me`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Unauthorized');
    } catch {
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
