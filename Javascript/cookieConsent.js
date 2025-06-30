// Simple cookie consent banner
// Displays a banner until the user accepts cookie usage
// Uses localStorage to remember consent

document.addEventListener('DOMContentLoaded', () => {
  const showBanner = () => {
    const existing = document.getElementById('cookie-consent');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'cookie-consent';
    banner.style.position = 'fixed';
    banner.style.bottom = '0';
    banner.style.left = '0';
    banner.style.right = '0';
    banner.style.padding = '1rem';
    banner.style.background = 'var(--banner-dark)';
    banner.style.color = 'var(--gold)';
    banner.style.textAlign = 'center';
    banner.style.zIndex = 'var(--z-index-toast)';
    banner.innerHTML =
      'This site uses cookies to enhance your experience. ' +
      '<button id="accept-cookies" class="royal-button">Accept</button> ' +
      '<button id="reject-cookies" class="royal-button">Reject</button>';

    document.body.appendChild(banner);

    document.getElementById('accept-cookies').addEventListener('click', () => {
      localStorage.setItem('cookieConsent', 'accepted');
      banner.remove();
    });

    document.getElementById('reject-cookies').addEventListener('click', () => {
      localStorage.setItem('cookieConsent', 'rejected');
      sessionStorage.removeItem('authToken');
      localStorage.removeItem('authToken');
      banner.remove();
    });
  };

  document.querySelectorAll('.site-footer').forEach((footer) => {
    if (footer.querySelector('#cookie-settings-link')) return;
    const link = document.createElement('a');
    link.href = '#';
    link.id = 'cookie-settings-link';
    link.textContent = 'Cookie Settings';
    link.style.marginLeft = '0.5rem';
    link.addEventListener('click', (e) => {
      e.preventDefault();
      showBanner();
    });
    const container = footer.lastElementChild || footer;
    container.append(' ', link);
  });

  if (localStorage.getItem('cookieConsent') !== 'accepted') {
    showBanner();
  }
});
