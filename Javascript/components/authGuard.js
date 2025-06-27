// Project Name: Thronestead©
// File Name: authGuard.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../../supabaseClient.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';
import { authJsonFetch } from '../utils.js';
import { startSessionRefresh } from '../auth.js';

// These values can be overridden by setting them on the global window object
// before this script is loaded. This allows pages to enforce additional access
// controls without modifying the guard itself.
const requireAdmin = window.requireAdmin === true;
const minVip = window.minVip || 0;
const requireAlliance = window.requireAlliance || false;
const requireRole = window.requireRole || null; // e.g. "officer", "leader"
const requirePermission = window.requirePermission || null; // e.g. "manage_projects"


(async () => {
  try {
    let token =
      localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    if (!token) {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        token = session.access_token;
        localStorage.setItem('authToken', token);
      } else {
        return (window.location.href = 'login.html');
      }
    }

    try {
      const res = await fetch('/api/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('unauthorized');
      const currentUser = await res.json();
      window.currentUser = currentUser;
      const storage =
        localStorage.getItem('authToken') === token ? localStorage : sessionStorage;
      storage.setItem('currentUser', JSON.stringify(currentUser));
      await authJsonFetch('/api/login/status');
    } catch {
      return (window.location.href = 'login.html');
    }

    let sessionUser;
    const {
      data: { user },
      error: userErr
    } = await supabase.auth.getUser();
    if (userErr) console.error('auth error:', userErr);
    sessionUser = user;

    if (!sessionUser || userErr) {
      const { data: refreshed, error: refreshErr } = await supabase.auth.refreshSession();
      if (!refreshed?.user || refreshErr) {
        return (window.location.href = "login.html");
      }
      sessionUser = refreshed.user;
    }

    startSessionRefresh();

    const { data: userData, error: userError } = await supabase
      .from("users")
      .select("is_admin, setup_complete")
      .eq("user_id", sessionUser.id)
      .single();

    if (!userData || userError || userData.setup_complete !== true) {
      // New account or not finished onboarding -> push to onboarding
      return (window.location.href = "play.html");
    }

    // ADMIN CHECK
    if (requireAdmin && userData.is_admin !== true) {
      alert("🚫 Admin only.");
      return (window.location.href = "overview.html");
    }

    // Retrieve VIP level from API
    let vipLevel = 0;
    try {
      const vipRes = await fetch('/api/kingdom/vip_status', {
        headers: { 'X-User-ID': sessionUser.id }
      });
      const vipData = await vipRes.json();
      vipLevel = vipData.vip_level || 0;
    } catch {
      vipLevel = 0;
    }

    if (vipLevel < minVip) {
      alert(`🚫 VIP Tier ${minVip}+ required.`);
      return (window.location.href = "overview.html");
    }

    // ALLIANCE ROLE
    const { data: alliance, error: allianceErr } = await supabase
      .from("alliance_members")
      .select("alliance_id, alliance_role, permissions")
      .eq("user_id", sessionUser.id)
      .single();

    // If alliance is required and not found
    if (requireAlliance && (!alliance || allianceErr)) {
      alert("🚫 You must be in an alliance.");
      return (window.location.href = "overview.html");
    }

    // If a specific role is required
    if (requireRole && alliance?.alliance_role !== requireRole) {
      alert(`🚫 ${requireRole} rank required.`);
      return (window.location.href = "overview.html");
    }

    // If a specific permission is required
    if (requirePermission && !alliance?.permissions?.includes(requirePermission)) {
      alert(`🚫 Permission '${requirePermission}' required.`);
      return (window.location.href = "overview.html");
    }

    // Store for page use
    window.user = {
      id: sessionUser.id,
      is_admin: userData.is_admin,
      vip_level: vipLevel,
      alliance_id: alliance?.alliance_id || null,
      alliance_role: alliance?.alliance_role || null,
      permissions: alliance?.permissions || []
    };

    // Hide any navbar items meant only for admins when the user isn't one.
    if (!userData.is_admin) {
      const hideAdminLinks = () => {
        const adminEls = document.querySelectorAll('.admin-only');
        if (adminEls.length) {
          adminEls.forEach((el) => el.remove());
          return true;
        }
        return false;
      };
      // Attempt immediately and also a few more times in case navbar loads late
      if (!hideAdminLinks()) {
        const interval = setInterval(() => {
          if (hideAdminLinks()) clearInterval(interval);
        }, 100);
        setTimeout(() => clearInterval(interval), 3000);
      }
    }

    loadPlayerProgressionFromStorage();
    if (!window.playerProgression) {
      await fetchAndStorePlayerProgression(sessionUser.id);
    }



  } catch (err) {
    console.error("🔥 Critical error:", err);
    window.location.href = "login.html";
  }
})();
