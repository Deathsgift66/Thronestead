// Project Name: Thronestead©
// File Name: signup.js
// Version 6.15.2025.21.00
// Developer: Deathsgift66
import {
  showToast,
  validateEmail,
  validatePasswordComplexity,
  debounce,
  toggleLoading
} from './utils.js';
import { supabase } from '../supabaseClient.js';
import { fetchAndStorePlayerProgression } from './progressionGlobal.js';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const bannedWords = ['admin', 'moderator', 'support'];

function validateUsername(name) {
  return /^[A-Za-z0-9]{3,20}$/.test(name);
}

function containsBannedWord(name) {
  const lower = name.toLowerCase();
  return bannedWords.some(w => lower.includes(w));
}
let signupButton;
let messageEl;
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById('signup-form');
  const kingdomNameEl = document.getElementById('kingdomName');
  const usernameEl = document.getElementById('username');
  signupButton = form.querySelector('button[type="submit"]');
  messageEl = document.getElementById('signup-message');

  // ✅ Debounced availability checker
  const check = debounce(checkAvailability, 400);
  kingdomNameEl.addEventListener('input', check);
  usernameEl.addEventListener('input', check);

  // ✅ Bind form submit
  form.addEventListener('submit', async (e) => {
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
  if (values.kingdomName.length < 3) return showMessage('Kingdom Name must be at least 3 characters.');
  if (containsBannedWord(values.kingdomName)) return showMessage('Chosen Kingdom Name is not allowed.');
  if (!validateUsername(values.username)) {
    return showMessage('Ruler Name must be 3-20 alphanumeric characters.');
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
        return showMessage('Email already exists.');
      }
      if (!data.username_available) {
        signupButton.disabled = false;
        signupButton.textContent = 'Seal Your Fate';
        return showMessage('Username already taken.');
      }
      if (!data.kingdom_available) {
        signupButton.disabled = false;
        signupButton.textContent = 'Seal Your Fate';
        return showMessage('Kingdom name already taken.');
      }
    }
  } catch (err) {
    console.error('Availability check failed', err);
    signupButton.disabled = false;
    signupButton.textContent = 'Seal Your Fate';
    return showMessage('Server error. Please try again.');
  }

  // ✅ Submit registration
  let captchaToken;
  try {
    captchaToken = await hcaptcha.execute();
  } catch (err) {
    signupButton.disabled = false;
    signupButton.textContent = 'Seal Your Fate';
    toggleLoading(false);
    return showToast("Captcha failed. Please try again.");
  }
  if (!captchaToken) {
    signupButton.disabled = false;
    signupButton.textContent = 'Seal Your Fate';
    toggleLoading(false);
    return showToast('Captcha failed. Please try again.');
  }

  const payload = {
    display_name: values.kingdomName,
    kingdom_name: values.kingdomName,
    username: values.username,
    email: values.email,
    password: values.password,
    captcha_token: captchaToken
  };

  try {
    const res = await fetch(`${API_BASE_URL}/api/signup/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }

    const data = await res.json();

    showToast('Sign-Up successful!');
    try {
      const { data: loginData, error } = await supabase.auth.signInWithPassword({
        email: values.email,
        password: values.password
      });
      if (!error && loginData?.session) {
        const token = loginData.session.access_token;
        const userInfo = loginData.user || {};
        sessionStorage.setItem('authToken', token);
        localStorage.setItem('authToken', token);
        sessionStorage.setItem('currentUser', JSON.stringify(userInfo));
        localStorage.setItem('currentUser', JSON.stringify(userInfo));
        await fetchAndStorePlayerProgression(userInfo.id);
      }
    } catch (loginErr) {
      console.error('Auto-login failed', loginErr);
    }
    setTimeout(() => (window.location.href = 'play.html'), 1200);
  } catch (err) {
    console.error("❌ Sign-Up error:", err);
    showMessage('Sign-Up failed. Please try again.');
  } finally {
    signupButton.disabled = false;
    signupButton.textContent = 'Seal Your Fate';
    toggleLoading(false);
  }
}

// ✅ Realtime check name availability
async function checkAvailability() {
  const kingdom = document.getElementById('kingdomName').value.trim();
  const user = document.getElementById('username').value.trim();
  if (!kingdom && !user) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/signup/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kingdom_name: kingdom, username: user })
    });

    if (!res.ok) return;
    const data = await res.json();
    updateAvailabilityUI('kingdomName-msg', data.kingdom_available);
    updateAvailabilityUI('username-msg', data.username_available);
  } catch (err) {
    console.error("Availability check failed", err);
  }
}

function updateAvailabilityUI(id, available) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = available ? "Available" : "Taken";
  el.className = 'availability ' + (available ? 'available' : 'taken');
}

function showMessage(text, type = 'error') {
  if (!messageEl) return;
  messageEl.textContent = text;
  messageEl.className = `message show ${type}-message`;
  setTimeout(() => {
    messageEl.classList.remove('show');
    messageEl.textContent = '';
  }, 5000);
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
