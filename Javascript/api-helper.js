// Project Name: Thronestead©
// File Name: apiHelper.js
// Version: 7/5/2025 20:00
// Developer: Generated

import { getStoredAuth } from './auth.js';

const API_BASE_URL =
  (typeof window !== 'undefined' && window.API_BASE_URL) ||
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  '';
const BACKUP_API_BASE_URL =
  (typeof window !== 'undefined' && window.BACKUP_API_BASE_URL) ||
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_BACKUP_API_BASE_URL) ||
  '';

async function request(path, options = {}, useBackup = false) {
  const { token } = getStoredAuth();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;
  const base = useBackup ? BACKUP_API_BASE_URL : API_BASE_URL;
  const res = await fetch(`${base}${path}`, { ...options, headers });
  if (
    res.status >= 500 &&
    !useBackup &&
    options.method === 'POST' &&
    BACKUP_API_BASE_URL
  ) {
    return request(path, options, true);
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export function apiGET(path, opts = {}) {
  return request(path, { ...opts, method: 'GET' });
}

export function apiPOST(path, body, opts = {}) {
  return request(path, { ...opts, method: 'POST', body: JSON.stringify(body) });
}

export function apiPATCH(path, body, opts = {}) {
  return request(path, { ...opts, method: 'PATCH', body: JSON.stringify(body) });
}

export function apiDELETE(path, opts = {}) {
  return request(path, { ...opts, method: 'DELETE' });
}
