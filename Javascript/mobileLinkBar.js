/*
Project Name: Kingmakers Rise Frontend
File Name: mobileLinkBar.js
Date: June 2, 2025
Author: Deathsgift66
*/
// mobileLinkBar.js — Handles mobile link bar interactions

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('mobile-menu-btn');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const toggle = document.querySelector('.dropdown-toggle');
    if (toggle) {
      toggle.click();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });
});
