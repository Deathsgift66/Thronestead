// Project Name: Thronestead©
// File Name: fetchJson.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { authFetch } from './utils.js';

/**
 * Internal helper to perform a fetch with abort/timeout support and JSON parsing.
 * @param {Function} fetcher fetch function to use
 * @param {string} url request URL
 * @param {RequestInit} options fetch options
 * @param {number} timeoutMs timeout in milliseconds
 */
async function fetchJsonInternal(fetcher, url, options, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetcher(url, {
      credentials: options.credentials || 'include',
      ...options,
      signal: controller.signal
    });

    const type = res.headers.get('content-type') || '';
    if (!res.ok) {
      const message = await res.text();
      if (res.status === 403 && message.toLowerCase().includes('banned')) {
        window.location.href = 'you_are_banned.html';
        throw new Error('Account banned');
      }
      if (res.status === 403) {
        throw new Error('Access denied (403)');
      }
      if (res.status === 504) {
        throw new Error('Server timeout (504)');
      }
      throw new Error(`Request failed (${res.status}): ${message || res.statusText}`);
    }
    if (!type.includes('application/json')) {
      throw new Error('Expected JSON response but got: ' + type);
    }
    return await res.json();
  } catch (err) {
    if (err.name === 'AbortError') throw new Error('Request timed out');
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Perform a fetch request expecting a JSON response.
 * The request is automatically aborted after `timeoutMs` milliseconds.
 *
 * @param {string} url            Target URL
 * @param {RequestInit} options   Fetch options
 * @param {number} timeoutMs      Timeout before aborting the request
 * @returns {Promise<any>}        Parsed JSON data
 */
export async function fetchJson(url, options = {}, timeoutMs = 8000) {
  return fetchJsonInternal(fetch, url, options, timeoutMs);
}

/**
 * Convenience wrapper for authenticated API requests.
 * Automatically includes Supabase auth headers using the stored session.
 *
 * @param {string} url            API endpoint
 * @param {RequestInit} [options] Additional fetch options
 * @param {number} [timeoutMs]    Optional timeout override
 * @returns {Promise<any>}        Parsed JSON data
 */
export async function authFetchJson(url, options = {}, timeoutMs = 8000) {
  return fetchJsonInternal(authFetch, url, options, timeoutMs);
}
