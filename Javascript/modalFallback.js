// Provides fallback implementations for modal and loading helpers
if (typeof window.openModal !== 'function') {
  window.openModal = id => {
    const el = typeof id === 'string' ? document.getElementById(id) : id;
    if (!el) return;
    el.classList.remove('hidden');
    el.setAttribute('aria-hidden', 'false');
    el.removeAttribute('inert');
    const focusable = el.querySelectorAll(
      'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const trap = e => {
      if (e.key === 'Escape') {
        window.closeModal(id);
      } else if (e.key === 'Tab' && focusable.length) {
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    el.__trapFocus = trap;
    el.addEventListener('keydown', trap);
    if (first) first.focus();
  };
}

if (typeof window.closeModal !== 'function') {
  window.closeModal = id => {
    const el = typeof id === 'string' ? document.getElementById(id) : id;
    if (!el) return;
    if (el.__trapFocus) el.removeEventListener('keydown', el.__trapFocus);
    delete el.__trapFocus;
    el.classList.add('hidden');
    el.setAttribute('aria-hidden', 'true');
    el.setAttribute('inert', '');
  };
}

if (typeof window.toggleLoading !== 'function') {
  window.toggleLoading = show => {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    overlay.setAttribute('aria-hidden', String(!show));
    overlay.style.display = show ? 'flex' : 'none';
  };
}
