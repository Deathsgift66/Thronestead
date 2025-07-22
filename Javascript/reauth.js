// Project Name: Thronestead©
// File Name: reauth.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// Component providing a modal prompt for reauthentication.

import { fetchJson } from './core_utils.js';
import { authHeaders } from './auth.js';
import { getEnvVar } from './env.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');

let token = null;

function readToken() {
  const match = document.cookie.match(/(?:^|; )reauthToken=([^;]+)/);
  token = match ? decodeURIComponent(match[1]) : null;
}

function saveToken(t, expSec) {
  token = t;
  const expiry = new Date(Date.now() + expSec * 1000).toUTCString();
  document.cookie =
    `reauthToken=${encodeURIComponent(token)}; path=/; secure; samesite=strict; domain=${location.hostname}; expires=${expiry}`;
}

export function clearReauthToken() {
  token = null;
  document.cookie =
    `reauthToken=; Max-Age=0; path=/; secure; samesite=strict; domain=${location.hostname};`;
}

export function getReauthHeaders() {
  if (!token) readToken();
  return token ? { 'X-Reauth-Token': token } : {};
}

export async function ensureReauth() {
  if (token) return token;
  readToken();
  if (token) return token;
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

  return new Promise(resolve => {
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
            otp: codeInput.value
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

