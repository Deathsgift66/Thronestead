// Project Name: Thronestead©
// File Name: apiHelper.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '../supabaseClient.js';
import { refreshSessionAndStore, clearStoredAuth } from './auth.js';

// ✅ Hardcoded fallback in case env fails
const API_BASE_URL = window?.env?.API_BASE_URL || 'https://thronestead.onrender.com';
const BACKUP_API_BASE_URL = window?.env?.BACKUP_API_BASE_URL || API_BASE_URL;

function cleanUrl(base, endpoint) {
  return `${base.replace(/\/+$/, '')}/${endpoint.replace(/^\/+/, '')}`;
}

async function getAuthToken() {
  try {
    const { data } = await supabase.auth.getSession();
    return data?.session?.access_token || null;
  } catch (err) {
    console.error('❌ Failed to get Supabase session:', err);
    return null;
  }
}

async function getHeaders(isJson = true) {
  const token = await getAuthToken();
  const headers = {};
  if (isJson) headers['Content-Type'] = 'application/json';
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

async function handleResponse(response) {
  const contentType = response.headers.get('content-type');
  const isJson = contentType?.includes('application/json');
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const msg = typeof data === 'string' ? data : data?.detail || 'Unknown error';
    throw new Error(`API Error (${response.status}): ${msg}`);
  }

  return data;
}

async function requestWithRetry(endpoint, options = {}, isJson = true) {
  let headers = await getHeaders(isJson);
  const fullUrl = cleanUrl(API_BASE_URL, endpoint);
  const backupUrl = cleanUrl(BACKUP_API_BASE_URL, endpoint);
  let response;

  try {
    response = await fetch(fullUrl, { ...options, headers });
  } catch (err) {
    console.warn('⚠️ Primary API fetch failed. Trying backup...', err);
    try {
      response = await fetch(backupUrl, { ...options, headers });
    } catch (backupErr) {
      console.error('❌ Backup API also failed:', backupErr);
      throw new Error('Both API endpoints unreachable.');
    }
  }

  // Handle 401: Attempt session refresh and retry
  if (response.status === 401) {
    try {
      const refreshed = await refreshSessionAndStore();
      if (refreshed) {
        headers = await getHeaders(isJson);
        response = await fetch(fullUrl, { ...options, headers });
      }
    } catch (err) {
      console.error('🔁 Session refresh failed:', err);
    }

    // If still 401 after refresh, force logout
    if (response.status === 401) {
      clearStoredAuth();
      if (!window.location.href.includes('login.html')) {
        window.location.href = 'login.html';
      }
      throw new Error('Unauthorized');
    }
  }

  // Retry failed responses (non-401) on backup if needed
  if (!response.ok && BACKUP_API_BASE_URL !== API_BASE_URL) {
    try {
      response = await fetch(backupUrl, { ...options, headers });
    } catch (err) {
      console.error('❌ Backup retry failed:', err);
    }
  }

  return handleResponse(response);
}

// ✅ Public API Wrappers
export async function apiGet(endpoint) {
  return requestWithRetry(endpoint, { method: 'GET' });
}

export async function apiPost(endpoint, body = {}) {
  return requestWithRetry(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function apiPut(endpoint, body = {}) {
  return requestWithRetry(endpoint, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

export async function apiDelete(endpoint) {
  return requestWithRetry(endpoint, { method: 'DELETE' });
}
