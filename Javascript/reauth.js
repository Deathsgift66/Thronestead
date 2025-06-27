// Project Name: Thronestead©
// File Name: reauth.js
// Version 6.19.2025.23.00
// Developer: Codex
// Component providing a modal prompt for reauthentication.

import { fetchJson } from './fetchJson.js';
import { authHeaders } from './auth.js';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

let token = sessionStorage.getItem('reauthToken') || null;
let expires = parseInt(sessionStorage.getItem('reauthExpires'), 10) || 0;

function saveToken(t, expSec) {
  token = t;
  expires = Date.now() + expSec * 1000;
  sessionStorage.setItem('reauthToken', token);
  sessionStorage.setItem('reauthExpires', String(expires));
}

export function clearReauthToken() {
  token = null;
  expires = 0;
  sessionStorage.removeItem('reauthToken');
  sessionStorage.removeItem('reauthExpires');
}

export function getReauthHeaders() {
  if (token && Date.now() < expires) {
    return { 'X-Reauth-Token': token };
  }
  clearReauthToken();
  return {};
}

export async function ensureReauth() {
  if (token && Date.now() < expires) return token;
  clearReauthToken();
  return await showReauthModal();
}

function buildModal() {
  const modal = document.createElement('div');
  modal.id = 'reauth-modal';
  modal.className = 'modal hidden';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-hidden', 'true');
  modal.setAttribute('inert', '');

  modal.innerHTML = `
    <div class="modal-content">
      <h2>Confirm Your Identity</h2>
      <p>Please re-enter your password or 2FA code.</p>
      <input type="password" id="reauth-password" placeholder="Password" autocomplete="current-password" />
      <input type="text" id="reauth-code" placeholder="2FA Code" autocomplete="one-time-code" />
      <button id="reauth-submit" class="royal-button">Verify</button>
      <div id="reauth-error" class="message error-message"></div>
    </div>`;
  document.body.appendChild(modal);
  return modal;
}

async function showReauthModal() {
  let modal = document.getElementById('reauth-modal');
  if (!modal) modal = buildModal();

  const pwdInput = modal.querySelector('#reauth-password');
  const codeInput = modal.querySelector('#reauth-code');
  const submitBtn = modal.querySelector('#reauth-submit');
  const errorBox = modal.querySelector('#reauth-error');

  return new Promise((resolve, reject) => {
    const cleanup = () => {
      modal.classList.add('hidden');
      modal.setAttribute('aria-hidden', 'true');
      modal.setAttribute('inert', '');
      submitBtn.removeEventListener('click', onSubmit);
    };

    async function onSubmit() {
      submitBtn.disabled = true;
      errorBox.textContent = '';
      try {
        const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' };
        const data = await fetchJson(`${API_BASE_URL}/api/reauth`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            password: pwdInput.value,
            code: codeInput.value
          })
        });
        if (!data?.token || !data?.expires_in) throw new Error('Invalid server response');
        saveToken(data.token, data.expires_in);
        cleanup();
        resolve(token);
      } catch (err) {
        errorBox.textContent = err.message || 'Reauthentication failed';
        submitBtn.disabled = false;
      }
    }

    modal.classList.remove('hidden');
    modal.removeAttribute('inert');
    modal.setAttribute('aria-hidden', 'false');
    pwdInput.value = '';
    codeInput.value = '';
    submitBtn.disabled = false;
    pwdInput.focus();

    submitBtn.addEventListener('click', onSubmit);
  });
}

export function setupReauthButtons(selector = '[data-require-reauth]') {
  document.addEventListener('click', async e => {
    const btn = e.target.closest(selector);
    if (!btn) return;
    if (btn.dataset.reauthDone) return;
    if (!getReauthHeaders()['X-Reauth-Token']) {
      e.preventDefault();
      e.stopImmediatePropagation();
      try {
        await ensureReauth();
        btn.dataset.reauthDone = '1';
        btn.click();
        delete btn.dataset.reauthDone;
      } catch (err) {
        console.warn('Reauth cancelled:', err);
      }
    }
  });
}

