// Project Name: Thronestead©
// File Name: fetchJson.js
// Version 6.15.2025.20.12
// Developer: Codex

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
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal
    });

    const contentType = res.headers.get('content-type') || '';
    if (!res.ok) {
      const message = await res.text();
      if (res.status === 403 && message.toLowerCase().includes('banned')) {
        window.location.href = 'you_are_banned.html';
        throw new Error('Account banned');
      }
      throw new Error(`Request failed (${res.status}): ${message || res.statusText}`);
    }
    if (!contentType.includes('application/json')) {
      throw new Error('Expected JSON response but got: ' + contentType);
    }

    return await res.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Request timed out');
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * Convenience wrapper for authenticated API requests.
 * Adds Authorization and X-User-ID headers using the provided session.
 *
 * @param {string} url            API endpoint
 * @param {object} session        Supabase session with `access_token` and `user.id`
 * @param {RequestInit} [options] Additional fetch options
 * @param {number} [timeoutMs]    Optional timeout override
 * @returns {Promise<any>}        Parsed JSON data
 */
export async function authFetchJson(url, session, options = {}, timeoutMs = 8000) {
  const headers = {
    ...(options.headers || {}),
    'Authorization': `Bearer ${session.access_token}`,
    'X-User-ID': session.user.id,
    'Content-Type': 'application/json'
  };

  return fetchJson(url, { ...options, headers }, timeoutMs);
}
