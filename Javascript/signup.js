// Project Name: Thronestead©
// File Name: signup.js
// Version 6.16.2025.21.02
// Developer: Deathsgift66
/* global hcaptcha */
import {
  showToast,
  validateEmail,
  validatePasswordComplexity,
  debounce,
  toggleLoading
} from './utils.js';
import { supabase } from '../supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';
import { containsBannedContent } from './content_filter.js';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || window.env?.API_BASE_URL || '';
if (!API_BASE_URL) {
  console.warn('⚠️ API_BASE_URL not set. API calls may fail.');
}
const reservedWords = ['admin', 'moderator', 'support'];

function validateUsername(name) {
  return /^[A-Za-z0-9]{3,20}$/.test(name);
}

function containsBannedWord(name) {
  const lower = name.toLowerCase();
  return reservedWords.some(w => lower.includes(w)) ||
    containsBannedContent(name);
}

function setFormDisabled(disabled) {
  if (!signupForm) return;
  signupForm.querySelectorAll('input, button').forEach(el => {
    el.disabled = disabled;
  });
}
let signupButton;
let messageEl;
let signupForm;
document.addEventListener("DOMContentLoaded", () => {
  signupForm = document.getElementById('signup-form');
  const kingdomNameEl = document.getElementById('kingdomName');
  const usernameEl = document.getElementById('username');
  signupButton = signupForm.querySelector('button[type="submit"]');
  messageEl = document.getElementById('signup-message');

  // ✅ Debounced availability checker
  const check = debounce(checkAvailability, 400);
  kingdomNameEl.addEventListener('input', check);
  usernameEl.addEventListener('input', check);

  // ✅ Bind form submit
  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleSignup();
  });

  // ✅ Show top kingdoms for social proof
  loadSignupStats();
});

// ✅ Signup flow handler
async function handleSignup() {
  const values = {
    kingdomName: document.getElementById('kingdomName').value.trim(),
    username: document.getElementById('username').value.trim(),
    email: document.getElementById('email').value.trim(),
    password: document.getElementById('password').value,
    confirmPassword: document.getElementById('confirmPassword').value,
    agreed: document.getElementById('agreeLegal').checked
  };
  if (messageEl) {
    messageEl.textContent = '';
    messageEl.className = 'message';
  }

  // ✅ Input validations
  if (!values.kingdomName) return showMessage('Kingdom Name is required.');
  if (values.kingdomName.length < 3) return showMessage('Kingdom Name must be at least 3 characters.');
  if (containsBannedWord(values.kingdomName)) {
    return showMessage('Chosen Kingdom Name is not allowed.');
  }
  if (!validateUsername(values.username)) {
    return showMessage('Ruler Name must be 3-20 alphanumeric characters.');
  }
  if (containsBannedWord(values.username)) {
    return showMessage('Ruler Name contains banned words.');
  }
  if (!validateEmail(values.email)) return showMessage('Invalid email address.');
  if (!validatePasswordComplexity(values.password)) {
    return showMessage('Password must include a number and symbol.');
  }
  if (values.password !== values.confirmPassword) return showMessage('Passwords do not match.');
  if (!values.agreed) return showMessage('You must agree to the legal terms.');

  if (!signupButton) return;
  signupButton.disabled = true;
  signupButton.textContent = 'Creating...';
  setFormDisabled(true);
  toggleLoading(true);

  // Check for duplicate email or username
  try {
    const availRes = await fetch(`${API_BASE_URL}/api/signup/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        kingdom_name: values.kingdomName,
        username: values.username,
        email: values.email
      })
    });
    if (availRes.ok) {
      const data = await availRes.json();
      if (!data.email_available) {
        signupButton.disabled = false;
        signupButton.textContent = 'Seal Your Fate';
        setFormDisabled(false);
        return showMessage('Email already exists.');
      }
      if (!data.username_available) {
        signupButton.disabled = false;
        signupButton.textContent = 'Seal Your Fate';
        setFormDisabled(false);
        return showMessage('Username already taken.');
      }
      if (!data.kingdom_available) {
        signupButton.disabled = false;
        signupButton.textContent = 'Seal Your Fate';
        setFormDisabled(false);
        return showMessage('Kingdom name already taken.');
      }
    }
  } catch (err) {
    console.error('Availability check failed', err);
    signupButton.disabled = false;
    signupButton.textContent = 'Seal Your Fate';
    setFormDisabled(false);
    return showMessage('Server error. Please try again.');
  }

  // ✅ Submit registration using Supabase
  let captchaToken;
  if (window.hcaptcha && typeof hcaptcha.getResponse === 'function') {
    captchaToken = hcaptcha.getResponse();
    if (!captchaToken) {
      signupButton.disabled = false;
      signupButton.textContent = 'Seal Your Fate';
      setFormDisabled(false);
      toggleLoading(false);
      return showToast('Please complete the captcha challenge.');
    }
  } else {
    // Development/testing without hCaptcha loaded
    captchaToken = 'test';
  }

  try {
    const { data: signUpData, error } = await supabase.auth.signUp({
      email: values.email,
      password: values.password,
      options: {
        data: {
          username: values.username,
          display_name: values.kingdomName
        }
      }
    });

    if (error) throw error;

    showToast('Sign-Up successful!');
    const session = signUpData.session;
    const userInfo = signUpData.user || {};
    const confirmed =
      userInfo.email_confirmed_at || userInfo.confirmed_at || false;

    if (confirmed) {
      if (session) {
        const token = session.access_token;
        sessionStorage.setItem('authToken', token);
        localStorage.setItem('authToken', token);
        try {
          await fetch(`${API_BASE_URL}/api/session/store`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ token })
          });
        } catch (err) {
          console.warn('Failed to persist session cookie:', err);
        }
      }
      if (userInfo.id) {
        sessionStorage.setItem('currentUser', JSON.stringify(userInfo));
        localStorage.setItem('currentUser', JSON.stringify(userInfo));
        try {
          const regRes = await fetch(`${API_BASE_URL}/api/signup/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: userInfo.id,
              email: values.email,
              username: values.username,
              kingdom_name: values.kingdomName,
              display_name: values.kingdomName,
              captcha_token: captchaToken
            })
          });
          if (!regRes.ok) {
            const data = await regRes.json().catch(() => ({}));
            throw new Error(data.detail || 'Registration failed');
          }
        } catch (err) {
          console.error('Finalize signup failed:', err);
          showMessage(err.message || 'Registration failed.');
          return;
        } finally {
          if (window.hcaptcha && typeof hcaptcha.reset === 'function') {
            hcaptcha.reset();
          }
        }
        await fetchAndStorePlayerProgression(userInfo.id);
      }
      setTimeout(() => (window.location.href = 'play.html'), 1200);
    } else {
      showToast('Check your email to verify your account.');
    }
  } catch (err) {
    console.error('❌ Sign-Up error:', err);
    showMessage(err.message || 'Sign-Up failed.');
  } finally {
    signupButton.disabled = false;
    signupButton.textContent = 'Seal Your Fate';
    setFormDisabled(false);
    toggleLoading(false);
  }
}

// ✅ Realtime check kingdom availability
async function checkAvailability() {
  const kingdom = document.getElementById('kingdomName').value.trim();
  const username = document.getElementById('username').value.trim();

  if (!kingdom && !username) {
    return;
  }

  if (kingdom && (kingdom.length < 3 ||
      containsBannedWord(kingdom))) {
    updateAvailabilityUI('kingdomName-msg', false);
    if (signupButton) signupButton.disabled = true;
    return;
  }
  if (username && (!validateUsername(username) || containsBannedWord(username))) {
    updateAvailabilityUI('username-msg', false);
    if (signupButton) signupButton.disabled = true;
    return;
  }

  try {
    const body = {};
    if (kingdom) body.kingdom_name = kingdom;
    if (username) body.username = username;
    const res = await fetch(`${API_BASE_URL}/api/signup/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error('check failed');
    const data = await res.json();

    if (kingdom) {
      updateAvailabilityUI('kingdomName-msg', data.kingdom_available);
    }
    if (username) {
      updateAvailabilityUI('username-msg', data.username_available);
    }

    if (signupButton) {
      signupButton.disabled =
        !data.kingdom_available || !data.username_available;
    }
  } catch (err) {
    console.error('Availability check failed', err);
    if (signupButton) signupButton.disabled = true;
  }
}

function updateAvailabilityUI(id, available) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = available ? "Available" : "Taken";
  el.className = 'availability ' + (available ? 'available' : 'taken');
}

function showMessage(text, type = 'error') {
  if (messageEl) {
    messageEl.textContent = text;
    messageEl.className = `message show ${type}-message`;
    setTimeout(() => {
      messageEl.classList.remove('show');
      messageEl.textContent = '';
    }, 5000);
  }
  showToast(text);
}

// ✅ Load top kingdom list (social proof)
async function loadSignupStats() {
  const panel = document.querySelector('.stats-panel');
  const list = document.getElementById('top-kingdoms-list');
  if (!panel || !list) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/signup/stats`);
    if (!res.ok) return;
    const data = await res.json();
    list.innerHTML = "";

    (data.top_kingdoms || []).forEach(k => {
      const li = document.createElement('li');
      li.textContent = `${k.kingdom_name} — Power ${k.score}`;
      list.appendChild(li);
    });

    panel.classList.remove('hidden');
  } catch (err) {
    console.error("Stats fetch failed", err);
  }
}
