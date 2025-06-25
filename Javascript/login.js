// Project Name: Thronestead©
// File Name: login.js
// Version 6.14.2025.21.00
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';

// DOM Elements
let loginForm, emailInput, passwordInput, loginButton, messageContainer;
let forgotLink, modal, closeBtn, sendResetBtn, forgotMessage;
let authLink, authModal, closeAuthBtn, sendAuthBtn, authMessage;
let announcementList;

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

  await loadAnnouncements();
});

// 🔐 Handle login form submission
async function handleLogin(e) {
  e.preventDefault();
  messageContainer.textContent = '🔐 Authenticating...';
  loginButton.disabled = true;
  loginButton.textContent = 'Entering Realm...';

  const email = emailInput.value.trim();
  const password = passwordInput.value;
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
    } else if (data?.user) {
      await fetchAndStorePlayerProgression(data.user.id);

      const token = data.session?.access_token;
      const statusRes = await fetch('/api/login/status', {
        headers: {
          'X-User-ID': data.user.id,
          Authorization: `Bearer ${token}`
        }
      });
      if (!statusRes.ok) {
        showMessage('error', 'Failed to check setup status.');
        return;
      }
      const statusData = await statusRes.json();
      const setupComplete = statusData?.setup_complete === true;

      showMessage('success', '✅ Login successful. Redirecting...');
      setTimeout(() => {
        window.location.href = setupComplete ? 'overview.html' : 'play.html';
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
