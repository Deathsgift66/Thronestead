// Project Name: Kingmakers Rise©
// File Name: allianceAppearance.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

const DEFAULT_BANNER = 'Assets/banner.png';

/**
 * Applies the alliance's banner, emblem, and background to matching page elements.
 */
async function applyAllianceAppearance() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const userId = session?.user?.id;
    if (!userId) return;

    const res = await fetch('/api/alliance-home/details', {
      headers: { 'X-User-ID': userId }
    });
    if (!res.ok) return;

    const data = await res.json();
    const alliance = data.alliance;
    if (!alliance) return;

    // Set banner (or fallback)
    const bannerURL = alliance.banner || DEFAULT_BANNER;
    document.querySelectorAll('.alliance-banner').forEach(img => {
      img.src = bannerURL;
    });

    // Set emblem if available
    if (alliance.emblem_url) {
      document.querySelectorAll('.alliance-emblem').forEach(img => {
        img.src = alliance.emblem_url;
      });
    }

    // Set background image if banner is valid
    if (alliance.banner) {
      document.querySelectorAll('.alliance-bg').forEach(el => {
        el.style.backgroundImage = `url(${bannerURL})`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundAttachment = 'fixed';
        el.style.backgroundRepeat = 'no-repeat';
        el.style.backgroundPosition = 'center';
      });
    }

  } catch (err) {
    console.error('❌ Alliance appearance load failed:', err);
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', applyAllianceAppearance);
