// Comment
// Project Name: Thronestead©
// File Name: tutorialModal.js
// Version: 7/1/2025 10:31
// Developer: Deathsgift66
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('tutorialModal');
  const closeBtn = document.getElementById('tutorialClose');
  const tabs = document.querySelectorAll('#tutorialModal .tab');
  const panels = document.querySelectorAll('#tutorialModal .tutorial-panel');
  const continueBtns = document.querySelectorAll('#tutorialModal .continue-btn');

  let currentStep = parseInt(getCookie('tutorialStep') || '0', 10);
  if (Number.isNaN(currentStep) || currentStep >= panels.length) currentStep = 0;

  showStep(currentStep);
  openModal();

  // Tab navigation
  tabs.forEach((tab, idx) => {
    tab.addEventListener('click', () => showStep(idx));
    tab.setAttribute('role', 'tab');
    tab.setAttribute('tabindex', '0');
    tab.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        showStep(idx);
        e.preventDefault();
      }
    });
  });

  continueBtns.forEach((btn, idx) => {
    btn.addEventListener('click', () => {
      if (idx < panels.length - 1) {
        showStep(idx + 1);
      } else {
        finishTutorial();
      }
    });
  });

  closeBtn.addEventListener('click', finishTutorial);

  function openModal() {
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.focus();
  }

  function finishTutorial() {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    setCookie('tutorialComplete', 'true', 60);
    if (typeof window.onTutorialComplete === 'function') {
      window.onTutorialComplete(); // Hook for tracking or syncing
    }
  }

  function showStep(n) {
    tabs.forEach((t, i) => {
      t.classList.toggle('active', i === n);
      t.setAttribute('aria-selected', i === n);
    });
    panels.forEach((p, i) => p.classList.toggle('active', i === n));
    setCookie('tutorialStep', n, 30);
    currentStep = n;
  }

  function setCookie(name, value, days) {
    try {
      const d = new Date();
      d.setTime(d.getTime() + days * 86400000);
      document.cookie =
        `${name}=${value}; expires=${d.toUTCString()}; path=/; domain=${location.hostname}; secure; samesite=strict`;
    } catch (err) {
      console.warn("Cookies are disabled or blocked:", err);
    }
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }
});
