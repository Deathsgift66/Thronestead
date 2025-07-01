// Comment
// Project Name: Thronestead©
// File Name: login.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { showToast } from './utils.js';

let loginForm = null,
  emailInput = null,
  passwordInput = null,
  loginButton = null,
  messageContainer = null,
  resetBtn = null,
  forgotEmail = null,
  forgotMessage = null;

document.addEventListener('DOMContentLoaded', async () => {
  loginForm = document.getElementById('login-form');
  emailInput = document.getElementById('login-email');
  passwordInput = document.getElementById('password');
  loginButton = document.querySelector('#login-form .royal-button');
  messageContainer = document.getElementById('message');
  resetBtn = document.getElementById('send-reset-btn');
  forgotEmail = document.getElementById('forgot-email');
  forgotMessage = document.getElementById('forgot-message');

  const session = (await supabase.auth.getSession()).data.session;
  if (session?.user) {
    await redirectToApp();
    return;
  }

  loginForm?.addEventListener('submit', handleLogin);
  resetBtn?.addEventListener('click', handleReset);
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

    // Session is persisted by Supabase client
    showMessage('success', 'Login successful. Redirecting...');
    setTimeout(() => redirectToApp(), 1200);
  } catch (err) {
    showMessage('error', err.message);
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

async function redirectToApp() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      return (window.location.href = 'overview.html');
    }

    const { data: profile } = await supabase
      .from('users')
      .select('setup_complete')
      .eq('user_id', user.id)
      .maybeSingle();

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
