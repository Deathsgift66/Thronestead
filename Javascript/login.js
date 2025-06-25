// Project Name: Thronestead©
// File Name: login.js
// Version 6.14.2025.21.01
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';
import { toggleLoading, authJsonFetch } from './utils.js';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// DOM Elements
let loginForm, emailInput, passwordInput, loginButton, messageContainer;
let forgotLink, modal, closeBtn, sendResetBtn, forgotMessage;
let authLink, authModal, closeAuthBtn, sendAuthBtn, authMessage;
let announcementList;
const ATTEMPT_LIMIT = 5;
const ATTEMPT_WINDOW = 5 * 60 * 1000;
const COOLDOWN_TIME = 10 * 60 * 1000;

function getAttemptData() {
  try {
    return JSON.parse(localStorage.getItem('loginAttempts')) || {};
  } catch {
    return {};
  }
}

function saveAttemptData(data) {
  localStorage.setItem('loginAttempts', JSON.stringify(data));
}

function clearAttempts() {
  localStorage.removeItem('loginAttempts');
}

function recordAttempt() {
  const now = Date.now();
  const data = getAttemptData();
  if (!data.first) {
    data.first = now;
    data.count = 1;
  } else if (now - data.first > ATTEMPT_WINDOW) {
    data.first = now;
    data.count = 1;
  } else {
    data.count = (data.count || 0) + 1;
  }
  if (data.count >= ATTEMPT_LIMIT) {
    data.blocked = now + COOLDOWN_TIME;
  }
  saveAttemptData(data);
}

function getCooldownMinutes() {
  const data = getAttemptData();
  if (data.blocked && Date.now() < data.blocked) {
    return Math.ceil((data.blocked - Date.now()) / 60000);
  }
  return 0;
}

document.addEventListener('DOMContentLoaded', async () => {
  loginForm = document.getElementById('login-form');
  emailInput = document.getElementById('login-email');
  passwordInput = document.getElementById('password');
  loginButton = document.querySelector('#login-form .royal-button');
  messageContainer = document.getElementById('message');

  announcementList = document.getElementById('announcement-list');
  forgotLink = document.getElementById('forgot-password-link');
  modal = document.getElementById('forgot-password-modal');
  closeBtn = document.getElementById('close-forgot-btn');
  sendResetBtn = document.getElementById('send-reset-btn');
  forgotMessage = document.getElementById('forgot-message');
  authLink = document.getElementById("request-auth-link");
  authModal = document.getElementById("auth-link-modal");
  closeAuthBtn = document.getElementById("close-auth-btn");
  sendAuthBtn = document.getElementById("send-auth-btn");
  authMessage = document.getElementById("auth-message");

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
  if (authLink) {
    authLink.addEventListener("click", e => {
      e.preventDefault();
      authModal.classList.remove("hidden");
      authMessage.textContent = "";
    });
  }

  if (closeAuthBtn) {
    closeAuthBtn.addEventListener("click", () => authModal.classList.add("hidden"));
  }

  if (sendAuthBtn) {
    sendAuthBtn.addEventListener("click", handleResendVerification);
  }

  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
  if (loginButton) {
    loginButton.addEventListener('click', handleLogin);
  }

  await loadAnnouncements();
});

// 🔐 Handle login form submission
async function handleLogin(e) {
  e.preventDefault();
  const cooldown = getCooldownMinutes();
  if (cooldown) {
    showMessage('error', `Too many attempts. Wait ${cooldown}m.`);
    return;
  }

  const email = emailInput.value.trim();
  const password = passwordInput.value;
  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  if (!email || !password || !emailValid) {
    showMessage('error', 'Please provide a valid email and password.');
    return;
  }

  messageContainer.textContent = '🔐 Authenticating...';
  loginButton.disabled = true;
  loginButton.textContent = 'Entering Realm...';
  toggleLoading(true);
  if (authLink) authLink.classList.add('hidden');

  try {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      const msg = error.message || '';
      if (msg.toLowerCase().includes('confirm')) {
        showMessage('error', '❌ Please verify your email before logging in.');
        if (authLink) authLink.classList.remove('hidden');
      } else {
        showMessage('error', '❌ Invalid credentials. Try again.');
      }
      recordAttempt();
    } else if (data?.user) {
      clearAttempts();
      let setupComplete = true;
      try {
        await fetchAndStorePlayerProgression(data.user.id);
        const statusData = await authJsonFetch(`${API_BASE_URL}/api/login/status`);
        setupComplete = statusData?.setup_complete === true;
      } catch (err) {
        console.error('Setup check failed:', err);
      }

      showMessage('success', '✅ Login successful. Redirecting...');
      setTimeout(() => {
        window.location.href = setupComplete ? 'overview.html' : 'play.html';
      }, 1200);
    }
  } catch (err) {
    showMessage('error', `Unexpected error: ${err.message}`);
    recordAttempt();
  } finally {
    resetLoginButton();
    toggleLoading(false);
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
      redirectTo: 'https://www.thronestead.com/forgot_password.html',
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
// 📨 Handle resend verification email
async function handleResendVerification() {
  const email = document.getElementById("auth-email").value.trim();
  if (!email) {
    authMessage.textContent = "Please enter a valid email.";
    return;
  }
  sendAuthBtn.disabled = true;
  sendAuthBtn.textContent = "Sending...";
  try {
    const { error } = await supabase.auth.resend({ type: "signup", email });
    if (error) {
      authMessage.textContent = "Error: " + error.message;
    } else {
      authMessage.textContent = "Verification email sent!";
    }
  } catch (err) {
    authMessage.textContent = `Unexpected error: ${err.message}`;
  } finally {
    sendAuthBtn.disabled = false;
    sendAuthBtn.textContent = "Send Verification Link";
  }
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
    const { data, error } = await supabase
      .from('announcements')
      .select('title, content')
      .eq('visible', true)
      .order('created_at', { ascending: false })
      .limit(5);

    if (error || !data || data.length === 0) {
      announcementList.innerHTML = '<li>No announcements yet.</li>';
      return;
    }

    announcementList.innerHTML = '';
    data.forEach(({ title, content }) => {
      const li = document.createElement('li');
      li.textContent = `\uD83D\uDCEF ${title}: ${content}`; // 📯 encoded for ES5 compatibility
      announcementList.appendChild(li);
    });
  } catch (err) {
    console.error('❌ Failed to load announcements:', err);
  }
}
