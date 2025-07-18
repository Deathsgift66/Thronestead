import { supabase } from '../../supabaseClient.js';
import { getEnvVar } from '../env.js';
import { startSessionRefresh } from '../auth.js';
import {
  fetchAndStorePlayerProgression,
  loadPlayerProgressionFromStorage,
} from '../progressionGlobal.js';
import { log } from '../logger.js'; // <-- New logging module

const PUBLIC_PATHS = new Set([
  '/index.html',
  '/about.html',
  '/projects.html',
  '/login.html',
  '/signup.html',
  '/update-password.html',
  '/legal.html',
  '/404.html',
]);

const ALLOWED_REDIRECTS = new Set([
  '/login.html',
  '/play.html',
  '/overview.html',
]);

const pathname = window.location.pathname.split('?')[0].split('#')[0];
const requireAdmin = document.querySelector('meta[name="require-admin"]')?.content === 'true';

// HTML visual shield placed directly in <head>, remove at end
document.documentElement.style.display = 'none';

(async function authGuard() {
  if (PUBLIC_PATHS.has(pathname)) {
    document.documentElement.style.display = '';
    return;
  }

  try {
    const session = await getValidSession();
    if (!session?.access_token) return redirect('/login.html');

    const API_BASE_URL = getEnvVar('API_BASE_URL');
    if (!API_BASE_URL) {
      document.body.innerHTML = `<div style="padding:50px;font-family:sans-serif;text-align:center;">
        <h1 style="color:red;">Configuration Error (API_BASE_URL Missing)</h1>
        <p>Please refresh or contact support immediately.</p>
      </div>`;
      throw new Error('Missing API_BASE_URL');
    }

    const authCheck = await fetchWithTimeout(`${API_BASE_URL}/api/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin',
    }, 5000);

    if (!authCheck.ok) return redirect('/login.html');

    let user = session.user;
    if (!user?.id) {
      const { data: { user: fallbackUser } = {}, error } = await supabase.auth.getUser();
      if (error || !fallbackUser?.id) return redirect('/login.html');
      user = fallbackUser;
    }

    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('is_admin, setup_complete')
      .eq('user_id', user.id)
      .single();

    if (!userData || userErr) {
      log.warn('User data fetch failed:', userErr);
      return redirect('/login.html');
    }
    if (!userData.setup_complete) {
      log.info('Profile incomplete, redirecting...');
      return redirect('/play.html');
    }
    if (requireAdmin && userData.is_admin !== true) {
      log.warn('Non-admin user attempted admin access.');
      return redirect('/overview.html');
    }

    window.user = window.user || Object.freeze({ id: user.id, is_admin: userData.is_admin });

    startSessionRefresh();

    try {
      loadPlayerProgressionFromStorage();
      if (!window.playerProgression) {
        await fetchAndStorePlayerProgression(user.id);
      }
    } catch (e) {
      log.warn('Progression load failed:', e);
    }

    log.info('Authentication successful:', user.id);

  } catch (err) {
    log.error('Fatal error:', err);
    redirect('/login.html');
  } finally {
    document.documentElement.style.display = '';
  }
})();
