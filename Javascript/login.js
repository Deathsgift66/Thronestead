/*
Project Name: Kingmakers Rise Frontend
File Name: login.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';

// Initialize Supabase Client

// DOM Elements
let loginForm;
let loginIdInput;
let passwordInput;
let loginButton;
let messageContainer;

// Forgot Password Modal Elements
let forgotLink;
let modal;
let closeBtn;
let sendResetBtn;
let forgotMessage;

document.addEventListener('DOMContentLoaded', () => {
  loginForm = document.getElementById('login-form');
  loginIdInput = document.getElementById('login-id');
  passwordInput = document.getElementById('password');
  loginButton = document.querySelector('#login-form .royal-button');
  messageContainer = document.getElementById('message');

  forgotLink = document.querySelector('.account-links a[href="forgot_password.html"]');
  modal = document.getElementById('forgot-password-modal');
  closeBtn = document.getElementById('close-forgot-btn');
  sendResetBtn = document.getElementById('send-reset-btn');
  forgotMessage = document.getElementById('forgot-message');

  if (forgotLink) {
    forgotLink.addEventListener('click', function (e) {
      e.preventDefault();
      modal.classList.remove('hidden');
      forgotMessage.textContent = ''; // Clear old messages
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', function () {
      modal.classList.add('hidden');
    });
  }

  if (sendResetBtn) {
    sendResetBtn.addEventListener('click', handleReset);
  }

  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
});

async function handleLogin(e) {
  e.preventDefault();
  loginButton.disabled = true;
  loginButton.textContent = 'Entering Realm...';

  const identifier = loginIdInput.value.trim();
  const password = passwordInput.value;

  let email = identifier;

  if (!isEmail(identifier)) {
    const { data: userData, error: userErr } = await supabase
      .from('users')
      .select('email')
      .eq('username', identifier)
      .single();
    if (userErr || !userData) {
      showMessage('error', 'User not found.');
      loginButton.disabled = false;
      loginButton.textContent = 'Enter the Realm';
      return;
    }
    email = userData.email;
  }

  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      showMessage('error', error.message);
    } else {
      const user = data.user;

      // On first login, create profile and starter kingdom
      const { data: profile } = await supabase
        .from('users')
        .select('user_id')
        .eq('user_id', user.id)
        .maybeSingle();

      if (!profile) {
        const { error: insertProfileErr } = await supabase
          .from('users')
          .insert({
            user_id: user.id,
            username: user.user_metadata.username,
            display_name: user.user_metadata.display_name,
            email: user.email,
            setup_complete: false
          });

        if (!insertProfileErr) {
          const { data: kingdomData, error: kingdomErr } = await supabase
            .from('kingdoms')
            .insert({ user_id: user.id, kingdom_name: user.user_metadata.display_name })
            .select('kingdom_id')
            .single();

          if (!kingdomErr) {
            await supabase
              .from('kingdom_resources')
              .insert({ kingdom_id: kingdomData.kingdom_id });
          }
        }
      }

      showMessage('success', 'Login successful! Redirecting...');
      await fetchAndStorePlayerProgression(user.id);
      setTimeout(() => {
        window.location.href = 'play.html';
      }, 1200);
    }
  } catch (err) {
    showMessage('error', `Unexpected error: ${err.message}`);
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = 'Enter the Realm';
  }
}

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
      redirectTo: 'https://www.kingmakersrise.com/update-password'
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

// Helper to check if string looks like an email
function isEmail(str) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(str);
}

// Show message function
function showMessage(type, text) {
  messageContainer.textContent = text;
  messageContainer.className = `message show ${type}-message`;
  setTimeout(() => {
    messageContainer.classList.remove('show');
    messageContainer.textContent = '';
  }, 5000);
}
