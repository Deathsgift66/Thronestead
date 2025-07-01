// Comment
// Project Name: Thronestead©
// File Name: mobileLinkBar.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('mobile-menu-btn');
  const dropdown = document.querySelector('.dropdown-toggle');
  const overlay = document.createElement('div');
  overlay.id = 'mobile-menu-overlay';
  overlay.style.position = 'fixed';
  overlay.style.top = 0;
  overlay.style.left = 0;
  overlay.style.width = '100vw';
  overlay.style.height = '100vh';
  overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
  overlay.style.zIndex = 998;
  overlay.style.display = 'none';
  document.body.appendChild(overlay);

  if (!toggleBtn || !dropdown) return;

  // Set accessibility attributes
  dropdown.setAttribute('role', 'menu');
  dropdown.setAttribute('aria-expanded', 'false');
  toggleBtn.setAttribute('aria-controls', 'mobile-menu');
  toggleBtn.setAttribute('aria-expanded', 'false');
  toggleBtn.setAttribute('aria-label', 'Toggle Mobile Menu');

  // Animate dropdown in/out
  function openDropdown() {
    dropdown.classList.add('open');
    dropdown.style.maxHeight = dropdown.scrollHeight + 'px';
    dropdown.setAttribute('aria-expanded', 'true');
    toggleBtn.setAttribute('aria-expanded', 'true');
    overlay.style.display = 'block';
    toggleBtn.innerHTML = '✖'; // Change icon to 'close'
  }

  function closeDropdown() {
    dropdown.classList.remove('open');
    dropdown.style.maxHeight = '0px';
    dropdown.setAttribute('aria-expanded', 'false');
    toggleBtn.setAttribute('aria-expanded', 'false');
    overlay.style.display = 'none';
    toggleBtn.innerHTML = '☰'; // Revert to 'hamburger'
  }

  toggleBtn.addEventListener('click', () => {
    dropdown.classList.contains('open') ? closeDropdown() : openDropdown();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // Outside click to close
  document.addEventListener('click', (e) => {
    if (!dropdown.classList.contains('open')) return;
    if (!dropdown.contains(e.target) && e.target !== toggleBtn) {
      closeDropdown();
    }
  });

  // Close on ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && dropdown.classList.contains('open')) {
      closeDropdown();
    }
  });

  // Overlay click closes menu
  overlay.addEventListener('click', closeDropdown);
});
