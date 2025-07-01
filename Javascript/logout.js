// Comment
// Project Name: Thronestead©
// File Name: logout.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
// Make sure supabase is available
import { supabase } from '../supabaseClient.js';
import { resetAuthCache, clearStoredAuth } from './auth.js';
import { clearReauthToken } from './reauth.js';

// Redirect helper used when clearing credentials
function logoutUser() {
  localStorage.removeItem('authToken');
  window.location.href = '/login.html';
}

// Logout function — clears session from Supabase, browser storage, and cookies
async function logout() {
  try {
    // 🔐 Supabase session sign-out
    await supabase.auth.signOut();
  } catch (err) {
    console.warn('Supabase logout error:', err.message);
  }

  // Clear stored credentials across tabs
  clearStoredAuth();
  resetAuthCache();
  clearReauthToken();

  // 🚪 Redirect to login
  logoutUser();
}

// Bind logout button (if present on page)
document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);
});
