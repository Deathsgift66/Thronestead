// Project Name: Thronestead©
// File Name: login.js (Simplified & Fixed)
// Version 7.01.2025.12.00
// Developer: Codex

import { supabase } from '../supabaseClient.js';
import { getEnvVar } from './env.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';
import { showToast } from './utils.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');

let loginForm = null,
  emailInput = null,
  passwordInput = null,
  loginButton = null,
  messageContainer = null;

document.addEventListener('DOMContentLoaded', async () => {
  loginForm = document.getElementById('login-form');
  emailInput = document.getElementById('login-email');
  passwordInput = document.getElementById('password');
  loginButton = document.querySelector('#login-form .royal-button');
  messageContainer = document.getElementById('message');

  const session = (await supabase.auth.getSession()).data.session;
  if (session?.user) return redirectToApp();

  loginForm?.addEventListener('submit', handleLogin);
});

async function handleLogin(e) {
  e.preventDefault();
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  if (!email || !password) return showMessage('error', 'Email and password required.');

  loginButton.disabled = true;
  loginButton.textContent = 'Entering Realm...';
  showMessage('info', 'Authenticating...');

  try {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error || !data?.session || !data.user) throw new Error(error?.message || 'Login failed.');

    if (!data.user.email_confirmed_at && !data.user.confirmed_at) {
      await supabase.auth.signOut();
      throw new Error('Email not confirmed.');
    }

    localStorage.setItem('authToken', data.session.access_token);
    localStorage.setItem('currentUser', JSON.stringify(data.user));

    await fetchAndStorePlayerProgression(data.user.id);
    showMessage('success', 'Login successful. Redirecting...');
    setTimeout(() => redirectToApp(), 1200);
  } catch (err) {
    showMessage('error', err.message);
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = 'Enter the Realm';
  }
}

function redirectToApp() {
  const params = new URLSearchParams(window.location.search);
  let target = params.get('redirect') || 'overview.html';
  if (!/^\/?[\w.-]+\.html$/.test(target)) target = 'overview.html';
  window.location.href = target;
}

function showMessage(type, text) {
  if (!messageContainer) return;
  messageContainer.textContent = text;
  messageContainer.className = `message show ${type}-message`;
  setTimeout(() => {
    messageContainer.textContent = '';
    messageContainer.classList.remove('show');
  }, 5000);
  showToast(text);
}
