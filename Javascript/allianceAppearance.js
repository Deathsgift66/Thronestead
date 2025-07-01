// Project Name: Thronestead©
// File Name: allianceAppearance.js
// Version 7.01.2025.08.00
// Developer: Codex (KISS Optimized)

import { supabase } from '../supabaseClient.js';

const DEFAULT_BANNER = '/Assets/banner.png';

async function applyAllianceAppearance() {
  try {
    const { data: { session } = {} } = await supabase.auth.getSession();
    const userId = session?.user?.id;
    if (!userId) return;

    const res = await fetch('/api/alliance-home/details', {
      headers: { 'X-User-ID': userId }
    });
    if (!res.ok) return;

    const { alliance } = await res.json();
    if (!alliance) return;

    const banner = alliance.banner || DEFAULT_BANNER;
    const emblem = alliance.emblem_url;

    // Update banner images
    document.querySelectorAll('.alliance-banner').forEach(img => {
      img.src = banner;
    });

    // Update emblem images
    if (emblem) {
      document.querySelectorAll('.alliance-emblem').forEach(img => {
        img.src = emblem;
      });
    }

    // Update background styles
    document.querySelectorAll('.alliance-bg').forEach(el => {
      el.style.backgroundImage = `url(${banner})`;
      el.style.backgroundSize = 'cover';
      el.style.backgroundAttachment = 'fixed';
      el.style.backgroundRepeat = 'no-repeat';
      el.style.backgroundPosition = 'center';
    });

  } catch (err) {
    console.error('❌ Failed to apply alliance appearance:', err);
  }
}

// 🚀 Initialize on load
document.addEventListener('DOMContentLoaded', applyAllianceAppearance);
