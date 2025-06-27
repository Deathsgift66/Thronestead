// Project Name: Thronestead©
// File Name: banAppeal.js
// Developer: Codex

import { fetchJson } from './fetchJson.js';
// import { initThemeToggle } from './themeToggle.js';

document.addEventListener('DOMContentLoaded', () => {
  // initThemeToggle();
  const form = document.getElementById('appeal-form');
  const emailInput = document.getElementById('appeal-email');
  const msgInput = document.getElementById('appeal-message');
  const messageEl = document.getElementById('appeal-status');

  form?.addEventListener('submit', async e => {
    e.preventDefault();
    const token = window.hcaptcha?.getResponse();
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
      if (window.hcaptcha && typeof hcaptcha.reset === 'function') {
        hcaptcha.reset();
      }
    } catch (err) {
      messageEl.textContent = err.message || 'Submission failed.';
      messageEl.className = 'message show error-message';
    }
  });
});
