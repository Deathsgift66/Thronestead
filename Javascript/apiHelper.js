// Project Name: Thronestead©
// File Name: apiHelper.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// Global Fetch Override for Thronestead
// Shows loading spinner + error toast on failed API calls
// Handles dev/prod routing via API_BASE

const originalFetch = window.fetch;

// ✅ Base URL switch for FastAPI depending on environment
const API_BASE =
  (window.ENV && window.ENV.API_BASE_URL)
    ? window.ENV.API_BASE_URL
    : window.API_BASE_URL ||
      'https://thronestead.onrender.com';

// ✅ Secondary backend used if the primary API_BASE fails
const FALLBACK_BASE = 'https://thronestead.onrender.com';

// ✅ Ensures loading overlay exists and returns reference
function getOverlay() {
  let el = document.getElementById('loading-overlay');
  if (!el) {
    el = document.createElement('div');
    el.id = 'loading-overlay';
    el.innerHTML = '<div class="spinner"></div>'; // spinner styling assumed in CSS
    document.body.appendChild(el);
  }
  return el;
}

// ✅ Creates and shows an error toast
function showError(message) {
  let box = document.getElementById('error-toast');
  if (!box) {
    box = document.createElement('div');
    box.id = 'error-toast';
    document.body.appendChild(box);
  }
  box.textContent = message;
  box.classList.add('show');
  setTimeout(() => box.classList.remove('show'), 3000); // hide after 3s
}

// ✅ Overrides native window.fetch
window.fetch = async function(url, options) {
  const overlay = getOverlay();
  overlay.classList.add('visible'); // show spinner

  const apiMatch = url.match(/^https?:\/\/[^/]+(\/api\/.*)/);
  const pathMatch = url.startsWith('/api/');
  const isApi = Boolean(apiMatch) || pathMatch;
  const apiPath = apiMatch ? apiMatch[1] : pathMatch ? url : '';
  const opts = { ...(options || {}), mode: 'cors' };

  const attempt = async (base) => {
    const fullUrl = isApi ? base + apiPath : url;
    return originalFetch(fullUrl, opts);
  };

  try {
    let res = await attempt(API_BASE);

    if (isApi && (!res.ok || res.status >= 500)) {
      try {
        const fallbackRes = await attempt(FALLBACK_BASE);
        if (fallbackRes.ok) {
          res = fallbackRes;
        }
      } catch (_) {
        // continue to error handling
      }
    }

    overlay.classList.remove('visible'); // hide spinner

    // If not successful, extract readable error text if available
    if (!res.ok) {
      const contentType = res.headers.get('Content-Type') || '';
      let errorText = '';

      if (contentType.includes('application/json')) {
        const json = await res.json();
        errorText = json.detail || json.message || res.statusText;
      } else {
        errorText = await res.text();
      }

      showError(errorText || res.statusText);
    }

    return res;
  } catch (err) {
    if (isApi) {
      try {
        const res = await attempt(FALLBACK_BASE);
        overlay.classList.remove('visible');

        if (!res.ok) {
          const contentType = res.headers.get('Content-Type') || '';
          let errorText = '';

          if (contentType.includes('application/json')) {
            const json = await res.json();
            errorText = json.detail || json.message || res.statusText;
          } else {
            errorText = await res.text();
          }

          showError(errorText || res.statusText);
        }

        return res;
      } catch (err2) {
        overlay.classList.remove('visible');
        showError('Network error. Please try again.');
        throw err2;
      }
    }
    overlay.classList.remove('visible');
    showError('Network error. Please try again.');
    throw err;
  }
};
