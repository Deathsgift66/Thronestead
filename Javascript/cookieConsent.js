// Project Name: Thronestead©
// File Name: cookieConsent.js
// Version 6.15.2025.21.00
// Developer: Deathsgift66

document.addEventListener('DOMContentLoaded', () => {
  if (localStorage.getItem('cookieConsent') === 'accepted') {
    enableAnalytics();
    return;
  }

  const banner = document.createElement('div');
  banner.id = 'cookie-banner';
  Object.assign(banner.style, {
    position: 'fixed',
    bottom: '0',
    left: '0',
    right: '0',
    padding: '1em',
    background: 'rgba(0, 0, 0, 0.9)',
    color: '#fff',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    zIndex: '10000'
  });

  const message = document.createElement('span');
  message.textContent = 'This site uses cookies for analytics. Accept?';
  banner.appendChild(message);

  const acceptBtn = document.createElement('button');
  acceptBtn.textContent = 'Accept';
  acceptBtn.style.marginLeft = '1em';
  acceptBtn.addEventListener('click', () => {
    localStorage.setItem('cookieConsent', 'accepted');
    enableAnalytics();
    banner.remove();
  });
  banner.appendChild(acceptBtn);

  document.body.appendChild(banner);
});

function enableAnalytics() {
  // Initialize your analytics here once consent is given
  window.analyticsEnabled = true;
}
