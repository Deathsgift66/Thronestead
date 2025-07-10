// Project Name: Thronestead©
// File Name: signup.js
// Version: 7.5.2025.21.00
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
import { getEnvVar } from './env.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');
if (!API_BASE_URL) {
  console.warn('⚠️ API_BASE_URL not set. API calls may fail.');
}

const reservedWords = ['admin', 'moderator', 'support'];

function normalizeWords(str) {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .split(/\s+/)
    .filter(Boolean);
}

function validateUsername(name) {
  // Allow spaces and symbols; just enforce length 3-32 characters
  const len = name.length;
  return len >= 3 && len <= 32;
}

function containsBannedWord(name) {
  const lower = name.toLowerCase();
  return reservedWords.some(w => lower === w || lower.startsWith(w)) ||
    containsBannedContent(name);

}

function updateAvailabilityUI(id, status) {
  const el = document.getElementById(id);
  if (!el) return;
  if (status === 'invalid') {
    el.textContent = 'Invalid';
    el.className = 'availability invalid';
    return;
  }
  const available = Boolean(status);
  el.textContent = available ? 'Available' : 'Taken';
  el.className = 'availability ' + (available ? 'available' : 'taken');
}

function showMessage(text, type = 'error') {
  const messageEl = document.getElementById('signup-message');
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

function setFormDisabled(disabled) {
  const form = document.getElementById('signup-form');
  form?.querySelectorAll('input, button').forEach(el => {
    el.disabled = disabled;
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const signupForm = document.getElementById('signup-form');
  const usernameEl = document.getElementById('kingdom_name');
  const emailEl = document.getElementById('email');
  const signupButton = signupForm.querySelector('button[type="submit"]');
  const check = debounce(checkAvailability, 400);
  usernameEl.addEventListener('input', check);
  emailEl.addEventListener('blur', checkEmailAvailability);
  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleSignup(signupButton);
  });
  loadSignupStats();
  loadRegions();
});

async function handleSignup(button) {
  const username = document.getElementById('kingdom_name').value.trim();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirmPassword').value;
  const region = document.getElementById('region').value.trim();
  const profile_bio = document.getElementById('profile_bio')?.value?.trim() || null;
  const agreed = document.getElementById('agreeLegal').checked;

  if (!validateUsername(username)) return showMessage('Kingdom Name must be 3–32 characters.');
  if (containsBannedWord(username)) return showMessage('Kingdom Name contains banned words.');
  if (!validateEmail(email)) return showMessage('Invalid email address.');
  if (!validatePasswordComplexity(password)) return showMessage('Password must include a number and a symbol.');
  if (password !== confirmPassword) return showMessage('Passwords do not match.');
  if (!region) return showMessage('Please select a region.');
  if (!agreed) return showMessage('You must agree to the legal terms.');

  button.disabled = true;
  button.textContent = 'Creating...';
  setFormDisabled(true);
  toggleLoading(true);

  try {
    const emailStatus = await checkEmailAvailability();
    if (emailStatus === false) {
      throw new Error('Email already exists.');
    }
    if (emailStatus === null) {
      throw new Error('Unable to verify email. Please try again later.');
    }

    const checkRes = await fetch(`${API_BASE_URL}/api/signup/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name: username, username, email })
    });
    if (!checkRes.ok) {
      throw new Error('Signup check failed');
    }
    const checkData = await checkRes.json();
    if (!checkData.email_available) {
      console.warn('EMAIL BLOCKED:', email, 'pre-check');
      throw new Error('Email already exists.');
    }
    if (!checkData.username_available) throw new Error('Kingdom name is taken.');

    let captchaToken = 'test';
    if (window.hcaptcha && typeof hcaptcha.getResponse === 'function') {
      captchaToken = hcaptcha.getResponse();
      if (!captchaToken) throw new Error('Please complete the captcha challenge.');
    }

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: 'https://www.thronestead.com/login.html',
        data: { username, display_name: username }
      }
    });

    if (error) {
      if (error.code === 'auth/email-already-in-use') {
        console.warn('EMAIL BLOCKED:', email, 'supabase');
        throw new Error('Email already exists.');
      }
      throw error;
    }

    const user = data.user;
    const confirmed = user?.email_confirmed_at || user?.confirmed_at;
    if (!confirmed) return showToast('Check your email to verify your account.');

    const regRes = await fetch(`${API_BASE_URL}/api/signup/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: user.id,
        email,
        kingdom_name: username,
        display_name: username,
        region,
        profile_bio,
        captcha_token: captchaToken
      })
    });

    if (!regRes.ok) {
      const errData = await regRes.json().catch(() => ({}));
      throw new Error(errData.detail || 'Registration failed');
    }

    sessionStorage.setItem('currentUser', JSON.stringify(user));
    localStorage.setItem('currentUser', JSON.stringify(user));
    await fetchAndStorePlayerProgression(user.id);

    showToast('Signup successful! Redirecting...');
    setTimeout(() => window.location.href = 'play.html', 1500);

  } catch (err) {
    console.error('❌ Signup error:', err);
    showMessage(err.message || 'Signup failed.');
  } finally {
    button.disabled = false;
    button.textContent = 'Seal Your Fate';
    setFormDisabled(false);
    toggleLoading(false);
    if (window.hcaptcha?.reset) hcaptcha.reset();
  }
}

async function checkAvailability() {
  const kingdom_name = document.getElementById('kingdom_name').value.trim();
  console.log('Checking name:', kingdom_name);
  console.log('validateUsername:', validateUsername(kingdom_name));
  console.log('containsBannedWord:', containsBannedWord(kingdom_name));
  if (!kingdom_name || !validateUsername(kingdom_name) || containsBannedWord(kingdom_name)) {
    updateAvailabilityUI('username-msg', 'invalid');
    document.querySelector('button[type="submit"]').disabled = true;
    return;
  }

  try {
    console.log(`Checking availability for: ${username}`);
    const res = await fetch(`${API_BASE_URL}/api/signup/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: kingdom_name, display_name: kingdom_name })
    });
    const data = await res.json();
    console.log('Availability result:', data);
    updateAvailabilityUI('username-msg', data.username_available);
    document.querySelector('button[type="submit"]').disabled = !data.username_available;
  } catch (err) {
    console.error('Availability check failed:', err);
  }
}

async function checkEmailAvailability() {
  const email = document.getElementById('email').value.trim();
  if (!email || !validateEmail(email)) {
    updateAvailabilityUI('email-msg', 'invalid');
    return null;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/signup/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    if (!res.ok) throw new Error(`status ${res.status}`);
    const data = await res.json();
    updateAvailabilityUI('email-msg', data.email_available);
    if (!data.email_available) {
      console.warn('EMAIL BLOCKED:', email, 'pre-check');
    }
    return data.email_available;
  } catch (err) {
    console.error('Email availability check failed:', err);
    updateAvailabilityUI('email-msg', 'invalid');
    return null;
  }
}

async function loadRegions() {
  const select = document.getElementById('region');
  const infoEl = document.getElementById('region-info');
  if (!select) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/kingdom/regions`);
    const regions = await res.json();
    select.innerHTML = '<option value="">Select Region</option>';
    regions.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.region_code;
      opt.textContent = r.region_name;
      select.appendChild(opt);
    });
    if (infoEl) {
      select.addEventListener('change', () => {
        const r = regions.find(x => x.region_code === select.value);
        infoEl.textContent = r?.description || '';
      });
    }
  } catch (err) {
    console.error('Failed to load regions:', err);
    select.innerHTML = '<option value="">Failed to load regions</option>';
  }
}

async function loadSignupStats() {
  const panel = document.querySelector('.stats-panel');
  const list = document.getElementById('top-kingdoms-list');
  if (!panel || !list) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/signup/stats`);
    if (!res.ok) return;
    const data = await res.json();
    list.innerHTML = '';
    (data.top_kingdoms || []).forEach(k => {
      const li = document.createElement('li');
      li.textContent = `${k.kingdom_name} — Power ${k.score}`;
      list.appendChild(li);
    });
    panel.classList.remove('hidden');
  } catch (err) {
    console.error('Failed to load top kingdoms:', err);
  }
}
