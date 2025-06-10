/*
Project Name: Kingmakers Rise Frontend
File Name: forgot_password.js
Date: June 2, 2025
Author: Deathsgift66
Updated: Enhanced interactivity and Supabase tips
*/

import { supabase } from './supabaseClient.js';

const requestForm = document.getElementById('request-form');
const emailInput = document.getElementById('email');
const codePanel = document.getElementById('code-panel');
const newPassPanel = document.getElementById('new-pass-panel');
const statusBanner = document.getElementById('status');
const resetCodeInput = document.getElementById('reset-code');
const newPasswordInput = document.getElementById('new-password');
const confirmPasswordInput = document.getElementById('confirm-password');
const strengthMeter = document.getElementById('strength-meter');
const tipsPanel = document.getElementById('tips-panel');
const tipsList = document.getElementById('tips-list');

requestForm.addEventListener('submit', (e) => {
  e.preventDefault();
  submitForgotRequest();
});

document.getElementById('verify-code-btn').addEventListener('click', submitResetCode);
document.getElementById('set-password-btn').addEventListener('click', submitNewPassword);
newPasswordInput.addEventListener('input', updateStrengthMeter);

async function submitForgotRequest() {
  const email = emailInput.value.trim();
  if (!email) {
    renderStatusMessage('Please enter a valid email.', true);
    return;
  }
  try {
    const res = await fetch('/api/auth/request-password-reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    if (res.ok) {
      renderStatusMessage('If the email exists, a reset link has been sent.', false);
    } else {
      const data = await res.json();
      renderStatusMessage(data.detail || 'Error sending reset request.', true);
    }
  } catch (err) {
    renderStatusMessage(err.message, true);
  }
}

async function submitResetCode() {
  const code = resetCodeInput.value.trim();
  if (!code) {
    renderStatusMessage('Enter the reset code.', true);
    return;
  }
  try {
    const res = await fetch('/api/auth/verify-reset-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    if (res.ok) {
      codePanel.classList.add('hidden');
      newPassPanel.classList.remove('hidden');
      renderStatusMessage('Code verified. Enter new password.', false);
    } else {
      const data = await res.json();
      renderStatusMessage(data.detail || 'Invalid or expired code.', true);
    }
  } catch (err) {
    renderStatusMessage(err.message, true);
  }
}

function validatePasswordMatch() {
  return newPasswordInput.value === confirmPasswordInput.value;
}

async function submitNewPassword() {
  if (!validatePasswordMatch()) {
    renderStatusMessage('Passwords do not match.', true);
    return;
  }
  const payload = {
    code: resetCodeInput.value.trim(),
    new_password: newPasswordInput.value,
    confirm_password: confirmPasswordInput.value
  };
  try {
    const res = await fetch('/api/auth/set-new-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      renderStatusMessage('Password updated! Redirecting...', false);
      setTimeout(() => {
        window.location.href = 'login.html';
      }, 8000);
    } else {
      const data = await res.json();
      renderStatusMessage(data.detail || 'Error updating password.', true);
    }
  } catch (err) {
    renderStatusMessage(err.message, true);
  }
}

function renderStatusMessage(msg, isError) {
  statusBanner.textContent = msg;
  statusBanner.classList.remove('success-banner', 'error-banner');
  statusBanner.classList.add(isError ? 'error-banner' : 'success-banner');
}

function calculateStrength(pw) {
  let score = 0;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

function updateStrengthMeter() {
  const score = calculateStrength(newPasswordInput.value);
  const percent = (score / 5) * 100;
  const color = score >= 4 ? 'var(--success)' : score >= 3 ? 'var(--warning)' : 'var(--error)';
  strengthMeter.innerHTML = `<div class="strength-meter-bar" style="width:${percent}%;background:${color}"></div>`;
}

async function loadSecurityTips() {
  try {
    const { data, error } = await supabase.from('security_tips').select('tip').limit(5);
    if (error) throw error;
    tipsList.innerHTML = '';
    data.forEach(row => {
      const li = document.createElement('li');
      li.textContent = row.tip;
      tipsList.appendChild(li);
    });
    tipsPanel.classList.remove('hidden');
  } catch (err) {
    console.warn('Failed to load tips');
  }
}

document.addEventListener('DOMContentLoaded', loadSecurityTips);

