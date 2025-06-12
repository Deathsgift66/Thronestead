const originalFetch = window.fetch;

// Base URL for API requests. When running the dev server on port 3000 we
// assume the FastAPI backend is available on localhost:8000.
const API_BASE =
  window.API_BASE_URL || (location.port === '3000' ? 'http://localhost:8000' : '');

function getOverlay() {
  let el = document.getElementById('loading-overlay');
  if (!el) {
    el = document.createElement('div');
    el.id = 'loading-overlay';
    el.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(el);
  }
  return el;
}

function showError(message) {
  let box = document.getElementById('error-toast');
  if (!box) {
    box = document.createElement('div');
    box.id = 'error-toast';
    document.body.appendChild(box);
  }
  box.textContent = message;
  box.classList.add('show');
  setTimeout(() => box.classList.remove('show'), 3000);
}

window.fetch = async function(url, options) {
  const overlay = getOverlay();
  overlay.classList.add('visible');
  try {
    const fullUrl = url.startsWith('/api/') ? API_BASE + url : url;
    const res = await originalFetch(fullUrl, options);
    overlay.classList.remove('visible');
    if (!res.ok) {
      const text = await res.text();
      showError(text || res.statusText);
    }
    return res;
  } catch (err) {
    overlay.classList.remove('visible');
    showError('Network error');
    throw err;
  }
};
