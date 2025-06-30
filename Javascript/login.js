// Project Name: Thronestead©
// File Name: login.js
// Version 6.19.2025.22.05
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';
import { toggleLoading, authJsonFetch, showToast, validateEmail } from './utils.js';
import {
  setAuthCache,
  clearStoredAuth,
  refreshSessionAndStore,
  authHeaders,
  startSessionRefresh,
} from './auth.js';
import { containsBannedContent } from './content_filter.js';
// import { initThemeToggle } from './themeToggle.js';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// DOM Elements
let loginForm, emailInput, passwordInput, loginButton, messageContainer,
  errorContainer;
let rememberCheckbox, togglePasswordBtn;
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

async function logAttempt(email, success) {
  try {
    await fetch(`${API_BASE_URL}/api/login/attempt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.toLowerCase(), success })
    });
  } catch (err) {
    console.warn('Failed to log login attempt:', err);
  }
}

// Wrapper to expose attempt logging under clearer name
function recordLoginAttempt(email, success) {
  logAttempt(email, success);
}

// Increase failed attempt count and block if threshold hit
function blockAfterFailedAttempts() {
  recordAttempt();
  const cooldown = getCooldownMinutes();
  if (cooldown) {
    showLoginError(`Too many attempts. Wait ${cooldown}m.`);
    return true;
  }
  return false;
}

// Redirect user after successful login
function redirectOnLogin(setupComplete) {
  const params = new URLSearchParams(window.location.search);
  let target = params.get('redirect');
  if (!target || target.includes('://') || target.startsWith('javascript:')) {
    target = setupComplete ? 'overview.html' : 'play.html';
  }
  window.location.href = target;
}

// Display login error message
function showLoginError(message) {
  if (errorContainer) {
    errorContainer.textContent = '';
    errorContainer.textContent = message;
  }
  showMessage('error', message);
}

// ✅ Validate login form inputs
function validateLoginInputs(email, password) {
  if (!email || !password) {
    return 'Email and password are required.';
  }
  if (!validateEmail(email)) {
    return 'Please enter a valid email address.';
  }
  if (password.length < 8) {
    return 'Password must be at least 8 characters.';
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
    if (!data.user?.email_confirmed_at && !data.user?.confirmed_at) {
      showMessage('error', 'Please verify your email before logging in.');
      await supabase.auth.signOut();
      return null;
    }
    const res = await fetch(`${API_BASE_URL}/api/session/store`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ token: data.session.access_token })
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      showMessage('error', text || '❌ Login failed.');
      return null;
    }
    return data;
  } catch (err) {
    showMessage('error', err.message || '❌ Login failed.');
    return null;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.user) {
    try {
      // Refresh the session token first in case it is stale
      await refreshSessionAndStore();

      let headers = await authHeaders();
      let res = await fetch(`${API_BASE_URL}/api/me`, { headers });

      if (!res.ok && res.status === 401) {
        const refreshed = await refreshSessionAndStore();
        if (refreshed) {
          headers = await authHeaders();
          res = await fetch(`${API_BASE_URL}/api/me`, { headers });
        }
      }

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
  togglePasswordBtn = document.getElementById('toggle-password');
  loginButton = document.querySelector('#login-form .royal-button');
  messageContainer = document.getElementById('message');
  errorContainer = document.getElementById('login-error');

  emailInput?.focus();

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

  // initThemeToggle();
  const allowPaste = window.env?.ALLOW_PASSWORD_PASTE === true;
  if (allowPaste) passwordInput.removeAttribute('onpaste');
  if (togglePasswordBtn) {
    togglePasswordBtn.addEventListener('click', () => {
      const hidden = passwordInput.type === 'password';
      passwordInput.type = hidden ? 'text' : 'password';
      togglePasswordBtn.setAttribute('aria-label', hidden ? 'Hide password' : 'Show password');
      togglePasswordBtn.setAttribute('aria-pressed', String(!hidden));
    });
  }

  if (forgotLink) {
    forgotLink.addEventListener('click', e => {
      e.preventDefault();
      modal.classList.remove('hidden');
      modal.removeAttribute('inert');
      modal.setAttribute('aria-hidden', 'false');
      document.getElementById('forgot-email')?.focus();
      forgotMessage.textContent = '';
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      modal.classList.add('hidden');
      modal.setAttribute('aria-hidden', 'true');
      modal.setAttribute('inert', '');
      forgotLink?.focus();
    });
  }

  if (sendResetBtn) {
    sendResetBtn.addEventListener('click', handleReset);
  }
  if (authLink) {
    authLink.addEventListener('click', e => {
      e.preventDefault();
      authModal.classList.remove('hidden');
      authModal.removeAttribute('inert');
      authModal.setAttribute('aria-hidden', 'false');
      document.getElementById('auth-email')?.focus();
      authMessage.textContent = '';
    });
  }

  if (closeAuthBtn) {
    closeAuthBtn.addEventListener('click', () => {
      authModal.classList.add('hidden');
      authModal.setAttribute('aria-hidden', 'true');
      authModal.setAttribute('inert', '');
      authLink?.focus();
    });
  }

  if (sendAuthBtn) {
    sendAuthBtn.addEventListener("click", handleResendVerification);
  }

  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }


  await loadAnnouncements();
});

// 🔐 Handle login form submission
async function handleLogin(e) {
  e.preventDefault();
  const cooldown = getCooldownMinutes();
  if (cooldown) {
    showLoginError(`Too many attempts. Wait ${cooldown}m.`);
    return;
  }

  const email = emailInput.value.trim();
  const password = passwordInput.value;
  const validationError = validateLoginInputs(email, password);
  if (validationError) {
    showLoginError(validationError);
    return;
  }
  // Only check the email for banned words. Passwords are user‑controlled and
  // may legitimately contain arbitrary character sequences that match entries
  // in the banned word list, so we avoid filtering them here.
  if (containsBannedContent(email)) {
    showLoginError('Input contains banned words.');
    return;
  }

  messageContainer.textContent = '🔐 Authenticating...';
  loginButton.disabled = true;
  loginButton.textContent = 'Entering Realm...';
  loginButton.classList.add('loading');
  toggleLoading(true);
  if (authLink) authLink.classList.add('hidden');

  try {
    const result = await loginExecute(email, password, rememberCheckbox?.checked);
    recordLoginAttempt(email, !!(result && result.user));
    if (!result) {
      if (authLink && messageContainer.textContent.includes('verify')) {
        authLink.classList.remove('hidden');
      }
      blockAfterFailedAttempts();
      emailInput.value = '';
      passwordInput.value = '';
    } else if (result.user) {
      clearAttempts();

      const storage = rememberCheckbox?.checked ? localStorage : sessionStorage;
      const altStorage = storage === localStorage ? sessionStorage : localStorage;

      const token = result.session?.access_token || '';
      let userInfo = result.user || {};

      // Persist credentials immediately so subsequent API calls succeed
      if (token) {
        const expiry = new Date(result.session.expires_at * 1000).toUTCString();
        document.cookie = `authToken=${token}; path=/; secure; samesite=strict; expires=${expiry}`;
      }
      storage.setItem('currentUser', JSON.stringify(userInfo));
      altStorage.removeItem('currentUser');
      setAuthCache(userInfo, result.session);
      startSessionRefresh();

      let setupComplete = true;
      try {
        await fetchAndStorePlayerProgression(result.user.id);
        const statusData = await authJsonFetch(`${API_BASE_URL}/api/login/status`);
        setupComplete = statusData?.setup_complete === true;

        const context = await authJsonFetch(`${API_BASE_URL}/api/me`);
        userInfo = { ...context, id: result.user.id };
        storage.setItem('currentUser', JSON.stringify(userInfo));
      } catch (err) {
        console.error('Setup check failed:', err);
      }

      showMessage('success', '✅ Login successful. Redirecting...');
      setTimeout(() => {
        redirectOnLogin(setupComplete);
      }, 1200);
    }
  } catch (err) {
    showLoginError(`Unexpected error: ${err.message}`);
    recordLoginAttempt(email, false);
    blockAfterFailedAttempts();
    emailInput.value = '';
    passwordInput.value = '';
  } finally {
    resetLoginButton();
    toggleLoading(false);
  }
}

// 🔁 Reset button state
function resetLoginButton() {
  loginButton.disabled = false;
  loginButton.textContent = 'Enter the Realm';
  loginButton.classList.remove('loading');
  if (errorContainer) errorContainer.textContent = '';
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
  if (messageContainer) {
    messageContainer.textContent = text;
    messageContainer.className = `message show ${type}-message`;
    setTimeout(() => {
      messageContainer.classList.remove('show');
      messageContainer.textContent = '';
    }, 5000);
  }
  showToast(text);
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
