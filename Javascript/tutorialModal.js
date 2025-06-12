/*
Project Name: Kingmakers Rise Frontend
File Name: tutorialModal.js
Updated: October 2025
Description: Modal-based tutorial with cookie progress.
*/

document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('tutorialModal');
  const closeBtn = document.getElementById('tutorialClose');
  const tabs = document.querySelectorAll('#tutorialModal .tab');
  const panels = document.querySelectorAll('#tutorialModal .tutorial-panel');
  const continueBtns = document.querySelectorAll('#tutorialModal .continue-btn');

  let step = parseInt(getCookie('tutorialStep') || '0', 10);
  if (Number.isNaN(step) || step >= panels.length) step = 0;

  showStep(step);
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');

  tabs.forEach((tab, idx) => {
    tab.addEventListener('click', () => showStep(idx));
  });

  continueBtns.forEach((btn, idx) => {
    btn.addEventListener('click', () => {
      if (idx < panels.length - 1) {
        showStep(idx + 1);
      } else {
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
      }
    });
  });

  closeBtn.addEventListener('click', () => {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
  });

  function showStep(n) {
    tabs.forEach(t => t.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    tabs[n].classList.add('active');
    panels[n].classList.add('active');
    setCookie('tutorialStep', n, 30);
  }

  function setCookie(name, value, days) {
    const d = new Date();
    d.setTime(d.getTime() + days * 86400000);
    document.cookie = `${name}=${value}; expires=${d.toUTCString()}; path=/`;
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }
});
