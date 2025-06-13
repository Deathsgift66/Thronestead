/*
Project Name: Kingmakers Rise Frontend
File Name: logout.js
Date: June 2, 2025
Author: Deathsgift66
*/

// Make sure supabase is available
import { supabase } from './supabaseClient.js';

// Logout function — clears session from Supabase, browser storage, and cookies
async function logout() {
  try {
    // 🔐 Supabase session sign-out
    await supabase.auth.signOut();
  } catch (err) {
    console.warn('Supabase logout error:', err.message);
  }

  // 🧹 Clear client-side storage
  sessionStorage.removeItem('authToken');
  localStorage.removeItem('authToken');

  // 🍪 Expire auth token cookie (if used)
  document.cookie = `authToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${window.location.hostname};`;

  // 🚪 Redirect to home/login
  window.location.href = 'index.html';
}

// Bind logout button (if present on page)
document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', logout);
});
