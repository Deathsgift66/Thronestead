/*
Project Name: Kingmakers Rise Frontend
File Name: tutorial.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Tutorial Page Controller — Scroll Animation Only

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  initScrollAnimations();
});

// ✅ Initialize Scroll Animations
function initScrollAnimations() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      } else {
        entry.target.classList.remove('visible');
      }
    });
  }, {
    threshold: 0.1
  });

  document.querySelectorAll('.tutorial-step').forEach(step => {
    observer.observe(step);
  });
}
