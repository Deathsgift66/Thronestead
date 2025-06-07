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
const loginForm = document.getElementById('login-form');
const loginIdInput = document.getElementById('login-id');
const passwordInput = document.getElementById('password');
const loginButton = document.querySelector('.royal-button');
const messageContainer = document.getElementById('message');

// Forgot Password Modal Elements
const forgotLink = document.querySelector('.account-links a[href="forgot_password.html"]');
const modal = document.getElementById('forgot-password-modal');
const closeBtn = document.getElementById('close-forgot-btn');
const sendResetBtn = document.getElementById('send-reset-btn');
const forgotMessage = document.getElementById('forgot-message');

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

// Handle Login Submit
loginForm.addEventListener('submit', async (e) => {
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
      showMessage('success', 'Login successful! Redirecting...');
      await fetchAndStorePlayerProgression(data.user.id);
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
});

// Intercept Forgot Password Link → open modal
forgotLink.addEventListener('click', function (e) {
  e.preventDefault();
  modal.classList.remove('hidden');
  forgotMessage.textContent = ''; // Clear old messages
});

// Close modal
closeBtn.addEventListener('click', function () {
  modal.classList.add('hidden');
});

// Send reset link
sendResetBtn.addEventListener('click', async function () {
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
});
