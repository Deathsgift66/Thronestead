// Project Name: Thronestead©
// File Name: banAppeal.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { fetchJson } from './core_utils.js';
import { validateEmail } from './core_utils.js';
import { getEnvVar } from './env.js';
import { initThemeToggle } from './themeToggle.js';

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  const form = document.getElementById('appeal-form');
  const emailInput = document.getElementById('appeal-email');
  const msgInput = document.getElementById('appeal-message');
  const messageEl = document.getElementById('appeal-status');
  const captchaEl = document.getElementById('appeal-captcha');

  if (!form || !emailInput || !msgInput || !messageEl || !captchaEl) return;

  const siteKey = getEnvVar('HCAPTCHA_SITEKEY');
  if (siteKey) {
    captchaEl.setAttribute('data-sitekey', siteKey);
  } else {
    console.warn('Missing hCaptcha site key');
  }

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      setTimeout(() => {
        submitBtn.disabled = false;
      }, 10000);
    }

    if (form.nickname?.value) return;

    if (!emailInput.value || !validateEmail(emailInput.value)) {
      messageEl.textContent = 'Enter a valid email address.';
      messageEl.className = 'message show error-message';
      return;
    }

    if (msgInput.value.trim().length < 10) {
      messageEl.textContent = 'Appeal message must be at least 10 characters.';
      messageEl.className = 'message show error-message';
      return;
    }

    const token = window.hcaptcha?.getResponse();
    if (!token) {
      messageEl.textContent = 'Please complete the CAPTCHA.';
      messageEl.className = 'message show error-message';
      return;
    }

    try {
      await fetchJson('/api/ban/appeal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: emailInput.value,
          message: msgInput.value,
          captcha_token: token
        })
      });
      messageEl.textContent = 'Appeal submitted successfully.';
      messageEl.className = 'message show success-message';
      form.reset();
      try {
        window.hcaptcha?.reset?.();
      } catch {}
    } catch (err) {
      messageEl.textContent = err.message || 'Submission failed.';
      messageEl.className = 'message show error-message';
    }
  });
});
