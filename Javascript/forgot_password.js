// Project Name: Thronestead©
// File Name: forgot_password.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// DOM Elements (assigned after DOMContentLoaded)
let requestForm;
let emailInput;
let codePanel;
let newPassPanel;
let statusBanner;
let resetCodeInput;
let newPasswordInput;
let confirmPasswordInput;
let strengthMeter;
let tipsPanel;
let tipsList;
let requestSubmitBtn;
let verifyCodeBtn;
let setPasswordBtn;

let accessToken = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', async () => {
  requestForm = document.getElementById('request-form');
  emailInput = document.getElementById('email');
  codePanel = document.getElementById('code-panel');
  newPassPanel = document.getElementById('new-pass-panel');
  statusBanner = document.getElementById('status');
  resetCodeInput = document.getElementById('reset-code');
  newPasswordInput = document.getElementById('new-password');
  confirmPasswordInput = document.getElementById('confirm-password');
  strengthMeter = document.getElementById('strength-meter');
  tipsPanel = document.getElementById('tips-panel');
  tipsList = document.getElementById('tips-list');
  requestSubmitBtn = requestForm?.querySelector('button[type="submit"]');
  verifyCodeBtn = document.getElementById('verify-code-btn');
  setPasswordBtn = document.getElementById('set-password-btn');

  loadSecurityTips();
  const params = new URLSearchParams(window.location.hash.substring(1));
  accessToken = params.get('access_token');
  if (accessToken) {
    const { error } = await supabase.auth.getUser(accessToken);
    if (error) {
      renderStatusMessage('Invalid or expired link.', true);
    } else {
      requestForm.classList.add('hidden');
      codePanel.classList.add('hidden');
      newPassPanel.classList.remove('hidden');
      newPassPanel.setAttribute('aria-hidden', 'false');
      renderStatusMessage('Enter your new password.', false);
    }
  }

  requestForm.addEventListener('submit', e => {
    e.preventDefault();
    submitForgotRequest();
  });
  verifyCodeBtn.addEventListener('click', submitResetCode);
  setPasswordBtn.addEventListener('click', submitNewPassword);
  newPasswordInput.addEventListener('input', updateStrengthMeter);
});

// ==========================
// Step 1: Request Reset Code
// ==========================
async function submitForgotRequest() {
  const email = emailInput.value.trim();
  if (!email) return renderStatusMessage('Please enter a valid email.', true);

  requestSubmitBtn.disabled = true;
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/request-password-reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });

    const msg = res.ok
      ? 'If the email exists, a reset link has been sent.'
      : (await res.json())?.detail || 'Error sending reset request.';
    renderStatusMessage(msg, !res.ok);
    if (res.ok) {
      codePanel.classList.remove('hidden');
      codePanel.setAttribute('aria-hidden', 'false');
    }
  } catch (err) {
    renderStatusMessage(err.message, true);
  } finally {
    requestSubmitBtn.disabled = false;
  }
}

// ==============================
// Step 2: Verify Reset Code
// ==============================
async function submitResetCode() {
  const code = resetCodeInput.value.trim();
  if (!code) return renderStatusMessage('Enter the reset code.', true);

  verifyCodeBtn.disabled = true;
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/verify-reset-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });

    if (res.ok) {
      codePanel.classList.add('hidden');
      codePanel.setAttribute('aria-hidden', 'true');
      newPassPanel.classList.remove('hidden');
      newPassPanel.setAttribute('aria-hidden', 'false');
      renderStatusMessage('Code verified. Enter new password.', false);
    } else {
      const data = await res.json();
      renderStatusMessage(data.detail || 'Invalid or expired code.', true);
    }
  } catch (err) {
    renderStatusMessage(err.message, true);
  } finally {
    verifyCodeBtn.disabled = false;
  }
}

// ================================
// Step 3: Set New Password
// ================================
async function submitNewPassword() {
  const new_password = newPasswordInput.value.trim();
  const confirm_password = confirmPasswordInput.value.trim();

  if (!validatePasswordMatch()) {
    return renderStatusMessage('Passwords do not match.', true);
  }
  if (calculateStrength(new_password) < 3) {
    return renderStatusMessage('Password too weak.', true);
  }

  setPasswordBtn.disabled = true;
  try {
    if (accessToken) {
      const { error } = await supabase.auth.updateUser(
        { password: new_password },
        { accessToken }
      );
      if (error) {
        renderStatusMessage('Reset failed', true);
        return;
      }
      renderStatusMessage('Password updated! Redirecting...', false);
      setTimeout(() => (window.location.href = 'login.html'), 5000);
    } else {
      const code = resetCodeInput.value.trim();
      const res = await fetch(`${API_BASE_URL}/api/auth/set-new-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, new_password, confirm_password })
      });

      if (res.ok) {
        renderStatusMessage('Password updated! Redirecting...', false);
        setTimeout(() => window.location.href = 'login.html', 5000);
      } else {
        const data = await res.json();
        renderStatusMessage(data.detail || 'Error updating password.', true);
      }
    }
  } catch (err) {
    renderStatusMessage(err.message, true);
  } finally {
    setPasswordBtn.disabled = false;
  }
}

// =======================
// UI Helpers
// =======================
function validatePasswordMatch() {
  return newPasswordInput.value === confirmPasswordInput.value;
}

function renderStatusMessage(message, isError = false) {
  statusBanner.textContent = message;
  statusBanner.className = `status-banner ${
    isError ? 'error-banner' : 'success-banner'
  }`;
}

// =======================
// Password Strength Meter
// =======================
function updateStrengthMeter() {
  const pw = newPasswordInput.value;
  const score = calculateStrength(pw);
  const percent = (score / 5) * 100;
  const color = score >= 4
    ? 'var(--success)'
    : score >= 3
      ? 'var(--warning)'
      : 'var(--error)';

  strengthMeter.innerHTML =
    `<div class="strength-meter-bar" style="width:${percent}%;background:${color}"></div>`;
}

function calculateStrength(password) {
  let score = 0;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  return score;
}

// ===========================
// Security Tips Loader
// ===========================
async function loadSecurityTips() {
  try {
    const { data, error } = await supabase
      .from('security_tips')
      .select('tip')
      .limit(5);

    if (error) throw error;

    tipsList.innerHTML = '';
    (data || []).forEach(row => {
      const li = document.createElement('li');
      li.textContent = row.tip;
      tipsList.appendChild(li);
    });
    tipsPanel.classList.remove('hidden');
  } catch {
    console.warn('⚠️ Unable to load security tips from Supabase.');
  }
}
