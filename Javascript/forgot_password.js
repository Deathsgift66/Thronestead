/*
Project Name: Kingmakers Rise Frontend
File Name: forgot_password.js
Date: June 2, 2025
Author: Deathsgift66
*/

const requestForm = document.getElementById('request-form');
const emailInput = document.getElementById('email');
const codePanel = document.getElementById('code-panel');
const newPassPanel = document.getElementById('new-pass-panel');
const statusBanner = document.getElementById('status');
const resetCodeInput = document.getElementById('reset-code');
const newPasswordInput = document.getElementById('new-password');
const confirmPasswordInput = document.getElementById('confirm-password');

requestForm.addEventListener('submit', (e) => {
  e.preventDefault();
  submitForgotRequest();
});

document.getElementById('verify-code-btn').addEventListener('click', submitResetCode);
document.getElementById('set-password-btn').addEventListener('click', submitNewPassword);

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

