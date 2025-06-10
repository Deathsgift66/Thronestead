import { supabase } from './supabaseClient.js';

async function applyAllianceAppearance() {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return;
  try {
    const res = await fetch('/api/alliance-home/details', {
      headers: { 'X-User-Id': session.user.id }
    });
    if (!res.ok) return;
    const data = await res.json();
    const a = data.alliance;
    if (!a) return;
    document.querySelectorAll('.alliance-banner').forEach(img => {
      img.src = a.banner || 'Assets/banner.png';
    });
    if (a.emblem_url) {
      document.querySelectorAll('.alliance-emblem').forEach(img => {
        img.src = a.emblem_url;
      });
    }
    if (a.banner) {
      document.querySelectorAll('.alliance-bg').forEach(el => {
        el.style.backgroundImage = `url(${a.banner})`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundAttachment = 'fixed';
      });
    }
  } catch (err) {
    console.error('Alliance appearance failed', err);
  }
}

document.addEventListener('DOMContentLoaded', applyAllianceAppearance);
