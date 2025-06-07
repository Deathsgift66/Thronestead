/*
Project Name: Kingmakers Rise Frontend
File Name: authGuard.js
Date: June 2, 2025
Author: Deathsgift66
*/
import { supabase } from '../supabaseClient.js';

const requireAdmin = false;
const minVip = 0;
const requireAlliance = false;
const requireRole = null; // e.g. "officer", "leader"
const requirePermission = null; // e.g. "manage_projects"

(async () => {
  try {
    const {
      data: { user },
      error: userErr
    } = await supabase.auth.getUser();

    if (!user) return (window.location.href = "login.html");

    const { data: userData, error: userError } = await supabase
      .from("users")
      .select("is_admin, vip_level")
      .eq("user_id", user.id)
      .single();

    if (!userData || userError) return (window.location.href = "login.html");

    // ADMIN/VIP
    if (requireAdmin && userData.is_admin !== true) {
      alert("🚫 Admin only.");
      return (window.location.href = "overview.html");
    }

    if (userData.vip_level < minVip) {
      alert(`🚫 VIP Tier ${minVip}+ required.`);
      return (window.location.href = "overview.html");
    }

    // ALLIANCE ROLE
    const { data: alliance, error: allianceErr } = await supabase
      .from("alliance_members")
      .select("alliance_id, alliance_role, permissions")
      .eq("user_id", user.id)
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
      id: user.id,
      is_admin: userData.is_admin,
      vip_level: userData.vip_level,
      alliance_id: alliance?.alliance_id || null,
      alliance_role: alliance?.alliance_role || null,
      permissions: alliance?.permissions || []
    };

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        await supabase.auth.signOut();
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = "index.html";
      });
    }

  } catch (err) {
    console.error("🔥 Critical error:", err);
    window.location.href = "login.html";
  }
})();
