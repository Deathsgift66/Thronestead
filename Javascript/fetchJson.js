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
