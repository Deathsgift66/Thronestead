/*
Project Name: Kingmakers Rise Frontend
File Name: login.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';

// DOM Elements
let loginForm, loginIdInput, passwordInput, loginButton, messageContainer;
let forgotLink, modal, closeBtn, sendResetBtn, forgotMessage, announcementList;

document.addEventListener('DOMContentLoaded', async () => {
  loginForm = document.getElementById('login-form');
  loginIdInput = document.getElementById('login-id');
  passwordInput = document.getElementById('password');
  loginButton = document.querySelector('#login-form .royal-button');
  messageContainer = document.getElementById('message');

  announcementList = document.getElementById('announcement-list');
  forgotLink = document.getElementById('forgot-password-link');
  modal = document.getElementById('forgot-password-modal');
  closeBtn = document.getElementById('close-forgot-btn');
  sendResetBtn = document.getElementById('send-reset-btn');
  forgotMessage = document.getElementById('forgot-message');

  if (forgotLink) {
    forgotLink.addEventListener('click', e => {
      e.preventDefault();
      modal.classList.remove('hidden');
      forgotMessage.textContent = '';
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
  }

  if (sendResetBtn) {
    sendResetBtn.addEventListener('click', handleReset);
  }

  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }

  await loadAnnouncements();
});

// 🔐 Handle login form submission
async function handleLogin(e) {
  e.preventDefault();
  loginButton.disabled = true;
  loginButton.textContent = 'Entering Realm...';

  const identifier = loginIdInput.value.trim();
  const password = passwordInput.value;

  let email = identifier;

  if (!isEmail(identifier)) {
    // Convert username to email
    const { data: userData, error } = await supabase
      .from('users')
      .select('email')
      .eq('username', identifier)
      .single();

    if (error || !userData) {
      showMessage('error', 'User not found.');
      resetLoginButton();
      return;
    }
    email = userData.email;
  }

  try {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      showMessage('error', error.message);
    } else if (data?.user) {
      await fetchAndStorePlayerProgression(data.user.id);

      const { data: details, error: setupErr } = await supabase
        .from('users')
        .select('setup_complete')
        .eq('user_id', data.user.id)
        .single();

      if (setupErr || !details) {
        showMessage('error', 'Failed to check setup status.');
        return;
      }

      showMessage('success', 'Login successful! Redirecting...');
      setTimeout(() => {
        window.location.href = details.setup_complete ? 'overview.html' : 'play.html';
      }, 1200);
    }
  } catch (err) {
    showMessage('error', `Unexpected error: ${err.message}`);
  } finally {
    resetLoginButton();
  }
}

// 🔁 Reset button state
function resetLoginButton() {
  loginButton.disabled = false;
  loginButton.textContent = 'Enter the Realm';
}

// 🧠 Handle password reset link
async function handleReset() {
  const email = document.getElementById('forgot-email').value.trim();
  if (!email) {
    forgotMessage.textContent = 'Please enter a valid email.';
    return;
  }

  sendResetBtn.disabled = true;
  sendResetBtn.textContent = 'Sending...';

  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: 'https://www.kingmakersrise.com/update-password',
    });

    if (error) {
      forgotMessage.textContent = 'Error: ' + error.message;
    } else {
      forgotMessage.textContent = 'Reset link sent! Check your email.';
    }
  } catch (err) {
    forgotMessage.textContent = `Unexpected error: ${err.message}`;
  } finally {
    sendResetBtn.disabled = false;
    sendResetBtn.textContent = 'Send Reset Link';
  }
}

// ✅ Simple email validator
function isEmail(str) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(str);
}

// 📣 Show banner messages
function showMessage(type, text) {
  messageContainer.textContent = text;
  messageContainer.className = `message show ${type}-message`;
  setTimeout(() => {
    messageContainer.classList.remove('show');
    messageContainer.textContent = '';
  }, 5000);
}

// 🗞 Load login page announcements
async function loadAnnouncements() {
  if (!announcementList) return;
  try {
    const res = await fetch('/api/login/announcements');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const ctype = res.headers.get('content-type') || '';
    if (!ctype.includes('application/json')) {
      const text = await res.text();
      console.error('❌ Announcements returned HTML instead of JSON');
      console.debug(text.slice(0, 150));
      return;
    }
    const announcements = await res.json();
    announcements.forEach((a) => {
      const li = document.createElement('li');
      li.textContent = `${a.title} - ${a.content}`;
      announcementList.appendChild(li);
    });
  } catch (err) {
    console.error('❌ Failed to load announcements:', err);
  }
}
