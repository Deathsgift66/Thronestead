// Project Name: Thronestead©
// File Name: authGuard.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../../supabaseClient.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';
import { authJsonFetch } from '../utils.js';
import { startSessionRefresh } from '../auth.js';

// Configurable per page
const requireAdmin = window.requireAdmin === true;
const minVip = window.minVip || 0;
const requireAlliance = window.requireAlliance || false;
const requireRole = window.requireRole || null;
const requirePermission = window.requirePermission || null;

(async () => {
  try {
    // ✅ Check if already logged in and visiting /login.html — redirect to overview
    if (window.location.pathname === '/login.html') {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (!error && session?.access_token) {
        return (window.location.href = '/overview.html');
      }
      // If no session, continue to login page
      return;
    }

    // ✅ Get current Supabase session
    const { data: { session }, error: sessionError } = await supabase.auth.getSession();
    if (sessionError || !session?.access_token) {
      console.warn('No Supabase session found – redirecting to login.');
      return (window.location.href = '/login.html');
    }

    const token = session.access_token;

    // ✅ Validate token with backend
    try {
      const res = await fetch('/api/me', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) {
        console.warn('Backend token rejected – redirecting to login.');
        return (window.location.href = '/login.html');
      }

      const currentUser = await res.json();
      window.currentUser = currentUser;
      sessionStorage.setItem('currentUser', JSON.stringify(currentUser));

      await authJsonFetch('/api/login/status');
    } catch (e) {
      console.warn('Error during backend session check:', e);
      return (window.location.href = '/login.html');
    }

    // ✅ Get Supabase user object
    let { data: { user: sessionUser }, error: userError } = await supabase.auth.getUser();
    if (!sessionUser || userError) {
      const { data: refreshed, error: refreshError } = await supabase.auth.refreshSession();
      if (!refreshed?.user || refreshError) {
        console.warn('Session refresh failed – redirecting to login.');
        return (window.location.href = '/login.html');
      }
      sessionUser = refreshed.user;
    }

    // ✅ Start Supabase session refresh
    startSessionRefresh();

    // ✅ Fetch user meta info
    const { data: userData, error: userDataError } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', sessionUser.id)
      .single();

    if (!userData || userDataError) {
      console.warn('Failed to load user record – redirecting.');
      return (window.location.href = '/login.html');
    }

    if (!userData.setup_complete) {
      return (window.location.href = '/play.html');
    }

    // ✅ Admin-only check
    if (requireAdmin && userData.is_admin !== true) {
      alert('🚫 Admins only.');
      return (window.location.href = '/overview.html');
    }

    // ✅ VIP level check
    let vipLevel = 0;
    try {
      const vipData = await authJsonFetch('/api/kingdom/vip_status');
      vipLevel = vipData?.vip_level || 0;
    } catch {
      vipLevel = 0;
    }

    if (vipLevel < minVip) {
      alert(`🚫 VIP Tier ${minVip}+ required.`);
      return (window.location.href = '/overview.html');
    }

    // ✅ Alliance check
    const { data: alliance, error: allianceError } = await supabase
      .from('alliance_members')
      .select('alliance_id, alliance_role, permissions')
      .eq('user_id', sessionUser.id)
      .single();

    if (requireAlliance && (!alliance || allianceError)) {
      alert('🚫 You must be in an alliance.');
      return (window.location.href = '/overview.html');
    }

    if (requireRole && alliance?.alliance_role !== requireRole) {
      alert(`🚫 ${requireRole} rank required.`);
      return (window.location.href = '/overview.html');
    }

    if (requirePermission && !alliance?.permissions?.includes(requirePermission)) {
      alert(`🚫 Permission '${requirePermission}' required.`);
      return (window.location.href = '/overview.html');
    }

    // ✅ Store user info globally
    window.user = {
      id: sessionUser.id,
      is_admin: userData.is_admin,
      vip_level: vipLevel,
      alliance_id: alliance?.alliance_id || null,
      alliance_role: alliance?.alliance_role || null,
      permissions: alliance?.permissions || []
    };

    // ✅ Hide admin-only UI if user isn't admin
    if (!userData.is_admin) {
      const hideAdminLinks = () => {
        const elements = document.querySelectorAll('.admin-only');
        elements.forEach(el => el.remove());
        return elements.length > 0;
      };
      if (!hideAdminLinks()) {
        const interval = setInterval(() => {
          if (hideAdminLinks()) clearInterval(interval);
        }, 100);
        setTimeout(() => clearInterval(interval), 3000);
      }
    }

    // ✅ Load player progression
    loadPlayerProgressionFromStorage();
    if (!window.playerProgression) {
      await fetchAndStorePlayerProgression(sessionUser.id);
    }

  } catch (err) {
    console.error('🔥 Critical authGuard failure:', err);
    window.location.href = '/login.html';
  }
})();
