export default function dialogPolyfill() {
  if ('HTMLDialogElement' in window) return;

  const focusable =
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

  document.querySelectorAll('dialog').forEach(dlg => {
    dlg.style.display = 'none';
    dlg.setAttribute('role', dlg.getAttribute('role') || 'dialog');
    dlg.setAttribute('aria-modal', 'true');

    if (!dlg.showModal) {
      dlg.showModal = function () {
        if (this.hasAttribute('open')) return;
        this.__prevActive = document.activeElement;
        this.setAttribute('open', '');
        this.style.display = 'block';
        const first = this.querySelector(focusable);
        (first || this).focus();
      };
    }

    if (!dlg.close) {
      dlg.close = function (returnValue) {
        if (!this.hasAttribute('open')) return;
        if (returnValue !== undefined) this.returnValue = String(returnValue);
        this.removeAttribute('open');
        this.style.display = 'none';
        if (this.__prevActive) this.__prevActive.focus();
        delete this.__prevActive;
      };
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      const dlg = document.querySelector('dialog[open]');
      if (dlg && typeof dlg.close === 'function') dlg.close();
    }
  });
}
