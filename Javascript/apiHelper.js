// Global Fetch Override for Kingmaker’s Rise
// Shows loading spinner + error toast on failed API calls
// Handles dev/prod routing via API_BASE

const originalFetch = window.fetch;

// ✅ Base URL switch for FastAPI depending on environment
const API_BASE =
  window.API_BASE_URL || (location.port === '3000' ? 'http://localhost:8000' : '');

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

  try {
    // If this is an API call, prepend base URL
    const fullUrl = url.startsWith('/api/') ? API_BASE + url : url;
    const res = await originalFetch(fullUrl, options);
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
    overlay.classList.remove('visible');
    showError('Network error. Please try again.');
    throw err;
  }
};
