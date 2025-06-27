// Simple cookie consent banner
// Displays a banner until the user accepts cookie usage
// Uses cookies to remember consent for one year

document.addEventListener('DOMContentLoaded', () => {
  if (document.cookie.includes('cookieConsent=true')) return;

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
  banner.innerHTML = 'This site uses cookies to enhance your experience. <button id="accept-cookies" class="royal-button">Accept</button>';

  document.body.appendChild(banner);
  document.getElementById('accept-cookies').addEventListener('click', () => {
    const d = new Date();
    d.setTime(d.getTime() + 365 * 86400000);
    document.cookie = `cookieConsent=true; expires=${d.toUTCString()}; path=/`;
    banner.remove();
  });
});
