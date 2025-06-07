/*
Project Name: Kingmakers Rise Frontend
File Name: index.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Hardened Landing Page — Dynamic CTA based on login state

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Enable smooth scroll
  enableSmoothScroll();

  // ✅ Validate session → update CTA
  await updateHeroCTA();

  // ✅ Optional: floating CTA on scroll
  setupFloatingCTA();
});

// ✅ Update Hero CTA based on login state
async function updateHeroCTA() {
  const { data: { session } } = await supabase.auth.getSession();

  // ✅ Main Hero Button
  const heroButton = document.querySelector(".hero-buttons a");

  if (!heroButton) return; // Safety

  if (session) {
    // Logged in → "Play Now"
    heroButton.textContent = "Play Now";
    heroButton.href = "play.html";
  } else {
    // Guest → "Join the Realm"
    heroButton.textContent = "Join the Realm";
    heroButton.href = "signup.html";
  }

  // ✅ Bottom CTA Button
  const ctaButton = document.querySelector(".cta-section a");

  if (!ctaButton) return; // Safety

  if (session) {
    // Logged in → "Continue Kingdom"
    ctaButton.textContent = "Continue Kingdom";
    ctaButton.href = "play.html";
  } else {
    // Guest → "Create Your Kingdom"
    ctaButton.textContent = "Create Your Kingdom";
    ctaButton.href = "signup.html";
  }
}

// ✅ Enable smooth scroll
function enableSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
}

// ✅ Floating CTA on scroll (optional polish)
function setupFloatingCTA() {
  const ctaSection = document.querySelector(".cta-section");

  if (!ctaSection) return;

  window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
      ctaSection.classList.add("sticky");
    } else {
      ctaSection.classList.remove("sticky");
    }
  });
}
