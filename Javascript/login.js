// Project Name: Thronestead©
// File Name: login.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { showToast, openModal, closeModal } from './utils.js';
import { getEnvVar } from './env.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');

function showModal(modalId) {
  openModal(modalId);
}

function hideModal(modalId) {
  closeModal(modalId);
}

let loginForm = null,
  emailInput = null,
  passwordInput = null,
  loginButton = null,
  messageContainer = null,
  resetBtn = null,
  forgotEmail = null,
  forgotMessage = null,
  togglePasswordBtn = null,
  loginErrorModal = null,
  loginErrorMessage = null,
  resendBtn = null,
  resendMsg = null,
  closeLoginErrorBtn = null,
  resendVerificationModal = null,
  resendEmailInput = null,
  resendVerificationMsg = null,
  sendVerificationBtn = null,
  closeVerificationBtn = null;

document.addEventListener('DOMContentLoaded', async () => {
  loginForm = document.getElementById('login-form');
  emailInput = document.getElementById('login-email');
  passwordInput = document.getElementById('password');
  loginButton = document.querySelector('#login-form .royal-button');
  messageContainer = document.getElementById('message');
  resetBtn = document.getElementById('send-reset-btn');
  forgotEmail = document.getElementById('forgot-email');
  forgotMessage = document.getElementById('forgot-message');
  togglePasswordBtn = document.getElementById('toggle-password');
  loginErrorModal = document.getElementById('login-error-modal');
  loginErrorMessage = document.getElementById('login-error-message');
  resendBtn = document.getElementById('resend-verification-btn');
  resendMsg = document.getElementById('resend-message');
  closeLoginErrorBtn = document.getElementById('close-login-error-btn');

  resendVerificationModal = document.getElementById('resend-verification-modal');
  resendEmailInput = document.getElementById('resend-email');
  resendVerificationMsg = document.getElementById('resend-verification-message');
  sendVerificationBtn = document.getElementById('send-verification-btn');
  closeVerificationBtn = document.getElementById('close-verification-btn');

  const forgotLink = document.getElementById('forgot-password-link');
  const forgotModal = document.getElementById('forgot-password-modal');
  const closeForgotBtn = document.getElementById('close-forgot-btn');
  const requestAuthLink = document.getElementById('request-auth-link');

  const session = (await supabase.auth.getSession()).data.session;
  if (session?.user) {
    await redirectToApp();
    return;
  }

  loginForm?.addEventListener('submit', handleLogin);
  resetBtn?.addEventListener('click', handleReset);
  togglePasswordBtn?.addEventListener('click', togglePassword);
  forgotLink?.addEventListener('click', (e) => {
    e.preventDefault();
    openModal(forgotModal);
  });
  closeForgotBtn?.addEventListener('click', () => closeModal(forgotModal));
  requestAuthLink?.addEventListener('click', (e) => {
    e.preventDefault();
    resendEmailInput.value = emailInput.value.trim();
    showModal('resend-verification-modal');
  });
  closeVerificationBtn?.addEventListener('click', () => hideModal('resend-verification-modal'));
  sendVerificationBtn?.addEventListener('click', handleVerificationResend);
  closeLoginErrorBtn?.addEventListener('click', () => {
    closeModal(loginErrorModal);
    resendBtn?.classList.add('hidden');
    resendMsg.textContent = '';
  });
  resendBtn?.addEventListener('click', resendVerification);
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
    const res = await fetch(`${API_BASE_URL}/api/login/authenticate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Login failed.');
    }
    const result = await res.json();
    if (result.access_token && result.refresh_token) {
      await supabase.auth.setSession({
        access_token: result.access_token,
        refresh_token: result.refresh_token
      });
      await supabase.auth.getSession();
      localStorage.setItem('authToken', result.access_token);
    }
    showMessage('success', 'Login successful. Redirecting...');
    setTimeout(() => redirectToApp(), 1200);
  } catch (err) {
    if (err.message === 'Email not confirmed') {
      if (loginErrorMessage) loginErrorMessage.textContent = err.message;
      resendBtn?.classList.remove('hidden');
      openModal(loginErrorModal);
    } else {
      showMessage('error', err.message);
    }
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = 'Enter the Realm';
  }
}

async function handleReset() {
  const email = forgotEmail.value.trim();
  if (!email) {
    forgotMessage.textContent = 'Enter a valid email.';
    return;
  }

  resetBtn.disabled = true;
  resetBtn.textContent = 'Sending...';

  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: 'https://www.thronestead.com/update-password.html',
    });
    forgotMessage.textContent = error ? error.message : 'Check your email!';
  } catch (err) {
    forgotMessage.textContent = err.message;
  } finally {
    resetBtn.disabled = false;
  resetBtn.textContent = 'Send Reset Link';
  }
}

function togglePassword() {
  if (!passwordInput) return;
  const visible = passwordInput.getAttribute('type') === 'text';
  passwordInput.setAttribute('type', visible ? 'password' : 'text');
  togglePasswordBtn.setAttribute('aria-pressed', String(!visible));
}

// Ensure the user's profile exists in the database.
async function ensureProfileRecord(user) {
  const { data: existing } = await supabase
    .from('users')
    .select('setup_complete')
    .eq('user_id', user.id)
    .maybeSingle();
  if (existing) return existing;

  const meta = user.user_metadata || {};
  try {
    await fetch(`${API_BASE_URL}/api/signup/finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: user.id,
        username: meta.username || '',
        display_name: meta.display_name || meta.username || 'New Ruler',
        kingdom_name: meta.display_name || meta.username || 'New Kingdom',
        email: user.email
      })
    });
  } catch (err) {
    console.error('Finalize signup error:', err);
  }
  const { data: refreshed } = await supabase
    .from('users')
    .select('setup_complete')
    .eq('user_id', user.id)
    .maybeSingle();
  return refreshed;
}

async function redirectToApp() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      return (window.location.href = 'overview.html');
    }

    const profile = await ensureProfileRecord(user);

    if (profile && profile.setup_complete === false) {
      window.location.href = 'play.html';
    } else {
      window.location.href = 'overview.html';
    }
  } catch (err) {
    console.error('Redirect failed:', err);
    window.location.href = 'overview.html';
  }
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


async function resendVerification() {
  const email = emailInput.value.trim();
  if (!email) {
    resendMsg.textContent = 'Enter your email above.';
    return;
  }
  resendBtn.disabled = true;
  resendMsg.textContent = '';
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/resend-confirmation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Failed to send email.');
    if (data.status === 'already_verified') {
      resendMsg.textContent = 'Email already verified.';
    } else {
      resendMsg.textContent = 'Verification email sent!';
    }
  } catch (err) {
    resendMsg.textContent = err.message;
  } finally {
    resendBtn.disabled = false;
  }
}

async function handleVerificationResend() {
  const email = resendEmailInput.value.trim();
  resendVerificationMsg.textContent = '';
  if (!email) {
    resendVerificationMsg.textContent = 'Please enter your email address.';
    return;
  }
  sendVerificationBtn.disabled = true;
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/resend-confirmation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Failed to send email.');
    if (data.status === 'already_verified') {
      resendVerificationMsg.textContent = 'Email already verified.';
    } else {
      resendVerificationMsg.textContent = '✅ Verification email sent!';
    }
  } catch (error) {
    resendVerificationMsg.textContent = `Error: ${error.message}`;
  } finally {
    sendVerificationBtn.disabled = false;
  }
}
