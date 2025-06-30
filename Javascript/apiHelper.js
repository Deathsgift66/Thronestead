import { supabase } from '../supabaseClient.js';
import { refreshSessionAndStore, clearStoredAuth } from './auth.js';
import { getEnvVar } from './env.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');
const BACKUP_API_BASE_URL = getEnvVar('BACKUP_API_BASE_URL');
if (!API_BASE_URL) {
  console.warn('⚠️ API_BASE_URL not set. API calls may fail.');
}
if (!BACKUP_API_BASE_URL) {
  console.warn('ℹ️ BACKUP_API_BASE_URL not set. Fallback POSTs disabled.');
}

async function getAuthToken() {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || null;
}

async function getHeaders(isJson = true) {
  const token = await getAuthToken();
  const headers = {};

  if (isJson) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function handleResponse(response) {
  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new Error(
      `API Error (${response.status}): ${typeof data === "string" ? data : data?.detail || "Unknown error"}`
    );
  }

  return data;
}

async function requestWithRetry(endpoint, options = {}, isJson = true) {
  let headers = await getHeaders(isJson);
  let response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status >= 500 && options.method === 'POST' && BACKUP_API_BASE_URL) {
    response = await fetch(`${BACKUP_API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
  }

  if (response.status === 401) {
    const refreshed = await refreshSessionAndStore();
    if (refreshed) {
      headers = await getHeaders(isJson);
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });
    }
    if (response.status === 401) {
      clearStoredAuth();
      window.location.href = 'login.html';
      throw new Error('Unauthorized');
    }
  }

  return handleResponse(response);
}

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
