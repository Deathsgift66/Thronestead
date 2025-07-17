export default function dialogPolyfill() {
  if ('HTMLDialogElement' in window) return;
  document.querySelectorAll('dialog').forEach(dlg => {
    if (!dlg.showModal) {
      dlg.showModal = function () {
        this.setAttribute('open', '');
      };
    }
    if (!dlg.close) {
      dlg.close = function () {
        this.removeAttribute('open');
      };
    }
  });
}
