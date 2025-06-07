const API_BASE_URL = window.API_BASE_URL || 'https://kingmakers-backend.onrender.com';

const originalFetch = window.fetch;
window.fetch = (input, init) => {
  if (typeof input === 'string' && input.startsWith('/')) {
    input = API_BASE_URL + input;
  }
  return originalFetch(input, init);
};
