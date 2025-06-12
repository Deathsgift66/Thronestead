export async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok || !res.headers.get('content-type')?.includes('application/json')) {
    throw new Error('Invalid JSON response');
  }
  return res.json();
}
