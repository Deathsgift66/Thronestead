// Project Name: Thronestead©
// File Name: login.js
// Version 6.20.2025.23.00
// Developer: Deathsgift66
import { supabase, supabaseReady } from '../supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';
import { getEnvVar } from './env.js';
import { toggleLoading, authJsonFetch, showToast, validateEmail } from './utils.js';
import { fetchJson } from './fetchJson.js';
import {
  setAuthCache,
  clearStoredAuth,
  refreshSessionAndStore,
  authHeaders,
  startSessionRefresh,
} from './auth.js';
import { containsBannedContent } from './content_filter.js';
// import { initThemeToggle } from './themeToggle.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');

// DOM Elements
let loginForm,
  emailInput,
  passwordInput,
  loginButton,
  messageContainer,
  errorContainer,
  errorModal,
  errorMessage,
  closeErrorBtn;
let rememberCheckbox, togglePasswordBtn;
let forgotLink, modal, closeBtn, sendResetBtn, forgotMessage;
let authLink, authModal, closeAuthBtn, sendAuthBtn, authMessage;
let announcementList;
const ATTEMPT_LIMIT = 5;
const ATTEMPT_WINDOW = 5 * 60 * 1000;
const COOLDOWN_TIME = 10 * 60 * 1000;

async function checkMaintenance() {
  try {
    const cfg = await fetchJson(`${API_BASE_URL}/api/public-config`);
    if (cfg?.MAINTENANCE_MODE || cfg?.FALLBACK_OVERRIDE) {
      showMessage('error', 'The realm is undergoing maintenance. Please return later.');
      loginForm?.classList.add('hidden');
      return true;
    }
  } catch (err) {
    console.warn('Maintenance check failed:', err);
  }
  return false;
}

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

function sendErrorContext(email, message) {
  const payload = {
    email: email || null,
    message,
    timestamp: Date.now(),
    user_agent: navigator.userAgent,
    platform: navigator.platform
  };
  fetch(`${API_BASE_URL}/api/login/error-context`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).catch(err => {
    console.warn('Failed to send error context:', err);
  });
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
function isValidRedirect(target) {
  if (!target || target.length > 100) return false;
  const lower = target.toLowerCase();
  if (lower.startsWith('javascript:')) return false;
  if (lower.includes('://') || lower.startsWith('//')) return false;
  if (/\s/.test(target)) return false;
  if (!/^[\w./-]+$/.test(target)) return false;
  if (lower === 'login.html') return false;
  return true;
}

function redirectOnLogin(setupComplete) {
  const params = new URLSearchParams(window.location.search);
  let target = params.get('redirect');
  if (!isValidRedirect(target)) {
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
  showErrorModal(message);
}

// ✅ Validate login form inputs
function validateLoginInputs(email, password) {
  if (!email || !password) return 'Email and password required.';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Invalid email.';
  return '';
}

// LOGIN_EXECUTE
// Sign user in and persist the session
export async function loginExecute(email, password, remember = false) {
  try {
    // Attempt server-side authentication first to catch banned/deleted users
    try {
      const { data: { session: curr } } = await supabase.auth.getSession();
      const token = curr?.access_token;
      const resp = await fetchJson(
        `${API_BASE_URL}/api/login/authenticate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          },
          body: JSON.stringify({ email, password })
        },
        8000
      );
      if (resp?.session) {
        await supabase.auth.setSession({
          access_token: resp.session.access_token,
          refresh_token: resp.session.refresh_token
        });
        return { user: resp.session.user, session: resp.session };
      }
    } catch (err) {
      console.warn('Backend auth failed:', err.message);
    }

    // Fallback to direct Supabase login with timeout
    let result;
    try {
      result = await Promise.race([
        supabase.auth.signInWithPassword({ email, password }),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('timeout')), 8000)
        )
      ]);
    } catch (err) {
      showMessage('error', 'Authentication service unreachable.');
      sendErrorContext(email, err.message);
      return null;
    }

    const { data, error } = result || {};
    if (error || !data?.session) {
      if (import.meta.env.DEV && error) {
        console.error('Supabase signIn error:', error);
      }
      const safeMessage = error && /invalid/i.test(error.message)
        ? error.message
        : '❌ Login failed.';
      showMessage('error', safeMessage);
      sendErrorContext(email, error?.message || 'sign-in failed');
      return null;
    }

    try {
      const refreshed = await supabase.auth.refreshSession();
      if (!refreshed.error && refreshed.data?.session) {
        data.session = refreshed.data.session;
      }
    } catch {
      // ignore refresh failure
    }

    if (!data.user?.email_confirmed_at && !data.user?.confirmed_at) {
      showMessage('error', 'Please verify your email before logging in.');
      await supabase.auth.signOut();
      return null;
    }

    // Session token is stored in localStorage only
    // to avoid mixing cookie and storage based auth
    // which can break session detection
    return data;
  } catch (err) {
    if (import.meta.env.DEV) {
      console.error('Login execution error:', err);
    }
    showMessage('error', err.message || '❌ Login failed.');
    sendErrorContext(email, err.message);
    return null;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  if (!supabaseReady || !supabase?.auth) {
    document.getElementById('main-content').innerHTML =
      '<p class="error-msg">Authentication service unavailable. Please try again later.</p>';
    console.error('Supabase failed to initialize');
    return;
  }

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
  errorModal = document.getElementById('login-error-modal');
  errorMessage = document.getElementById('login-error-message');
  closeErrorBtn = document.getElementById('close-login-error-btn');

  if (await checkMaintenance()) {
    return;
  }

  // initThemeToggle();
  const allowPaste =
    getEnvVar('ALLOW_PASSWORD_PASTE', 'false').toLowerCase() === 'true';
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

  if (closeErrorBtn) {
    closeErrorBtn.addEventListener('click', () => {
      errorModal.classList.add('hidden');
      errorModal.setAttribute('aria-hidden', 'true');
      errorModal.setAttribute('inert', '');
      loginButton?.focus();
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
    loginForm.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const err = validateLoginInputs(email, password);
        if (err) {
          e.preventDefault();
          showLoginError(err);
        }
      }
    });
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

      const storage = localStorage;
      const altStorage = sessionStorage;

      const token = result.session?.access_token || '';
      let userInfo = result.user || {};

      // Persist credentials immediately so subsequent API calls succeed
        if (token) {
          localStorage.setItem('authToken', token);
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
    if (import.meta.env.DEV) {
      console.error('Login handler error:', err);
    }
    showLoginError(`Unexpected error: ${err.message}`);
    sendErrorContext(email, err.message);
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
      if (import.meta.env.DEV) console.error('Reset password error:', error);
      forgotMessage.textContent = 'Error: ' + error.message;
    } else {
      forgotMessage.textContent = 'Reset link sent! Check your email.';
    }
  } catch (err) {
    if (import.meta.env.DEV) console.error('Reset link failed:', err);
    forgotMessage.textContent = `Unexpected error: ${err.message}`;
    sendErrorContext(email, err.message);
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
      if (import.meta.env.DEV) console.error('Resend verification error:', error);
      authMessage.textContent = "Error: " + error.message;
    } else {
      authMessage.textContent = "Verification email sent!";
    }
  } catch (err) {
    if (import.meta.env.DEV) console.error('Resend verification failed:', err);
    authMessage.textContent = `Unexpected error: ${err.message}`;
    sendErrorContext(email, err.message);
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

function showErrorModal(message) {
  if (!errorModal || !errorMessage) return;
  errorMessage.textContent = message;
  errorModal.classList.remove('hidden');
  errorModal.removeAttribute('inert');
  errorModal.setAttribute('aria-hidden', 'false');
  closeErrorBtn?.focus();
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
