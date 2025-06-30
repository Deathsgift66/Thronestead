// Simple cookie consent banner
// Displays a banner until the user accepts cookie usage
// Uses localStorage to remember consent

document.addEventListener('DOMContentLoaded', () => {
  const applyConsent = (consent) => {
    if (consent === 'rejected') {
      document.cookie =
        'authToken=; Max-Age=0; path=/; secure; samesite=strict;';
    }
  };

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
      applyConsent('accepted');
      banner.remove();
      updateToggle(true);
    });

    document.getElementById('reject-cookies').addEventListener('click', () => {
      localStorage.setItem('cookieConsent', 'rejected');
      document.cookie =
        `authToken=; Max-Age=0; path=/; secure; samesite=strict; domain=${location.hostname};`;
      applyConsent('rejected');
      banner.remove();
      updateToggle(false);
    });
  };

  const createToggle = () => {
    const label = document.createElement('label');
    label.id = 'consent-toggle';
    label.className = 'consent-toggle';
    label.style.marginLeft = '0.5rem';
    label.style.display = 'inline-flex';
    label.style.alignItems = 'center';
    label.style.gap = '0.25rem';
    label.textContent = 'Allow cookies';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.setAttribute('aria-label', 'Toggle cookie consent');
    checkbox.checked = localStorage.getItem('cookieConsent') === 'accepted';
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) {
        localStorage.setItem('cookieConsent', 'accepted');
        applyConsent('accepted');
      } else {
        localStorage.setItem('cookieConsent', 'rejected');
        applyConsent('rejected');
      }
    });
    label.prepend(checkbox);
    return label;
  };

  const updateToggle = (checked) => {
    document.querySelectorAll('#consent-toggle input').forEach((el) => {
      el.checked = checked;
    });
  };

  document.querySelectorAll('.site-footer').forEach((footer) => {
    const container = footer.lastElementChild || footer;

    if (!footer.querySelector('#cookie-settings-link')) {
      const link = document.createElement('a');
      link.href = '#';
      link.id = 'cookie-settings-link';
      link.textContent = 'Cookie Settings';
      link.style.marginLeft = '0.5rem';
      link.addEventListener('click', (e) => {
        e.preventDefault();
        showBanner();
      });
      container.append(' ', link);
    }

    if (!footer.querySelector('#consent-toggle')) {
      container.append(' ', createToggle());
    }
  });

  if (localStorage.getItem('cookieConsent') !== 'accepted') {
    showBanner();
  } else {
    applyConsent('accepted');
  }
});
