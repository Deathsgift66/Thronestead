const originalFetch = window.fetch;

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
    const res = await originalFetch(url, options);
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
