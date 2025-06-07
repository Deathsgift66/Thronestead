/*
Project Name: Kingmakers Rise Frontend
File Name: donate_vip.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Hardened VIP/Donate Page — Stripe Flow

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout (optional — if using navbar inject)
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load — Bind VIP buttons
  bindVipButtons();
});

// ✅ Bind VIP buttons
function bindVipButtons() {
  document.querySelectorAll('.donate-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tier = mapButtonToTier(btn.id);

      if (!tier) {
        alert("Invalid VIP tier.");
        return;
      }

      try {
        const { data: { user } } = await supabase.auth.getUser();

        const res = await fetch("/api/stripe/create-checkout-session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tier,
            user_id: user.id
          })
        });

        const result = await res.json();

        if (!res.ok || !result.session_url) {
          throw new Error(result.error || "Failed to create checkout session.");
        }

        // ✅ Redirect to Stripe checkout
        window.location.href = result.session_url;

      } catch (err) {
        console.error("❌ Error starting checkout:", err);
        alert("Failed to start checkout. Please try again.");
      }
    });
  });
}

// ✅ Map button ID → VIP Tier
function mapButtonToTier(buttonId) {
  switch (buttonId) {
    case 'vip1-btn': return 'VIP1';
    case 'vip2-btn': return 'VIP2';
    case 'vip3-btn': return 'VIP3';
    default: return null;
  }
}
