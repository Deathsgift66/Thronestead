import { supabase } from '../supabaseClient.js';

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session && !window.location.href.includes('login')) {
    window.location.href = '/game.html';
  }
});
