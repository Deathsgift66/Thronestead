// Project Name: Thronestead©
// File Name: login.js
// Version 6.17.2025.21.04
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';
import { toggleLoading, authJsonFetch } from './utils.js';
import { validateEmail } from './utils.js';
import { setAuthCache, clearStoredAuth } from './auth.js';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// DOM Elements
let loginForm, emailInput, passwordInput, loginButton, messageContainer;
let rememberCheckbox;
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

// ✅ Validate login form inputs
function validateLoginInputs(email, password) {
  if (!email || !password) {
    return 'Email and password are required.';
  }
  if (!validateEmail(email)) {
    return 'Please enter a valid email address.';
  }
  return '';
}

// LOGIN_EXECUTE
// Sign user in and persist the session
export async function loginExecute(email, password, remember = false) {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    });
    if (error || !data?.session) {
      showMessage('error', error?.message || '❌ Invalid credentials.');
      return null;
    }
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem('authToken', data.session.access_token);
    return data;
  } catch (err) {
    showMessage('error', err.message || '❌ Login failed.');
    return null;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  const storedToken =
    localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
  if (session?.user && storedToken) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/me`, {
        headers: { Authorization: `Bearer ${storedToken}` }
      });
      if (res.ok) {
        return (window.location.href = 'overview.html');
      }
    } catch (err) {
      console.warn('Auto-login check failed:', err);
    }
    clearStoredAuth();
  }
  loginForm = document.getElementById('login-form');
  emailInput = document.getElementById('login-email');
  passwordInput = document.getElementById('password');
  rememberCheckbox = document.getElementById('remember-me');
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
  const validationError = validateLoginInputs(email, password);
  if (validationError) {
    showMessage('error', validationError);
    return;
  }

  messageContainer.textContent = '🔐 Authenticating...';
  loginButton.disabled = true;
  loginButton.textContent = 'Entering Realm...';
  toggleLoading(true);
  if (authLink) authLink.classList.add('hidden');

  try {
    const result = await loginExecute(email, password, rememberCheckbox?.checked);
    if (!result) {
      if (authLink && messageContainer.textContent.includes('verify')) {
        authLink.classList.remove('hidden');
      }
      recordAttempt();
    } else if (result.user) {
      clearAttempts();
      let setupComplete = true;
      let token = result.session?.access_token || '';
      try {
        await fetchAndStorePlayerProgression(result.user.id);

        const statusData = await authJsonFetch(`${API_BASE_URL}/api/login/status`);
        setupComplete = statusData?.setup_complete === true;

      } catch (err) {
        console.error('Setup check failed:', err);
      }

      let userInfo = result.user || {};
      try {
        userInfo = await authJsonFetch(`${API_BASE_URL}/api/me`);
      } catch (err) {
        console.warn('Failed to load user context:', err);
      }

      const storage = rememberCheckbox?.checked ? localStorage : sessionStorage;
      const altStorage = storage === localStorage ? sessionStorage : localStorage;
      storage.setItem('authToken', token);
      storage.setItem('currentUser', JSON.stringify(userInfo));
      altStorage.removeItem('authToken');
      altStorage.removeItem('currentUser');

      // Update in-memory auth cache for current page
      setAuthCache(userInfo, result.session);

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
      redirectTo: 'https://www.thronestead.com/update-password.html',
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
