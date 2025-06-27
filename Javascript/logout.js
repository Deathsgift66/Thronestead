// Project Name: Thronestead©
// File Name: logout.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// Make sure supabase is available
import { supabase } from '../supabaseClient.js';
import { resetAuthCache } from './auth.js';
import { clearReauthToken } from './reauth.js';

// Logout function — clears session from Supabase, browser storage, and cookies
async function logout() {
  try {
    // 🔐 Supabase session sign-out
    await supabase.auth.signOut();
  } catch (err) {
    console.warn('Supabase logout error:', err.message);
  }

  // Clear cached auth so next page load fetches fresh session
  resetAuthCache();
  clearReauthToken();

  // 🧹 Clear client-side storage
  sessionStorage.removeItem('authToken');
  localStorage.removeItem('authToken');

  // 🍪 Expire auth token cookie (if used)
  document.cookie = `authToken=; Max-Age=0; path=/; Secure; HttpOnly; SameSite=Strict;`;

  // 🚪 Redirect to home/login
  window.location.href = 'index.html';
}

// Bind logout button (if present on page)
document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);
});
