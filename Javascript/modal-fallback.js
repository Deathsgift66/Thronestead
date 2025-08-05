// Provides fallback implementations for modal and loading helpers
if (typeof window.openModal !== 'function') {
  window.openModal = modal => {
    const el = typeof modal === 'string' ? document.getElementById(modal) : modal;
    if (!el) return;
    el.__prevFocus = document.activeElement;
    el.classList.remove('hidden');
    el.removeAttribute('hidden');
    el.setAttribute('aria-hidden', 'false');
    el.removeAttribute('inert');

    const focusable = el.querySelectorAll(
      'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    const trap = e => {
      if (e.key === 'Escape') {
        window.closeModal(el);
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

    const outside = e => {
      if (e.target === el) window.closeModal(el);
    };

    el.__trapFocus = trap;
    el.__outsideClick = outside;
    el.addEventListener('keydown', trap);
    el.addEventListener('click', outside);
    if (first) first.focus();
  };
}

if (typeof window.closeModal !== 'function') {
  window.closeModal = modal => {
    const el = typeof modal === 'string' ? document.getElementById(modal) : modal;
    if (!el) return;
    if (el.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    if (el.__trapFocus) el.removeEventListener('keydown', el.__trapFocus);
    if (el.__outsideClick) el.removeEventListener('click', el.__outsideClick);
    delete el.__trapFocus;
    delete el.__outsideClick;
    el.classList.add('hidden');
    el.setAttribute('hidden', '');
    el.setAttribute('aria-hidden', 'true');
    el.setAttribute('inert', '');
    if (el.__prevFocus && typeof el.__prevFocus.focus === 'function') {
      el.__prevFocus.focus();
    }
    delete el.__prevFocus;
  };
}

if (typeof window.toggleLoading !== 'function') {
  window.toggleLoading = show => {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.toggle('visible', show);
    document.body.classList.toggle('loading', show);
  };
}
