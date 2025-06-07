/*
Project Name: Kingmakers Rise Frontend
File Name: legal.js
Date: June 2, 2025
Author: Deathsgift66
*/
// legal.js - Handles loading and dynamic interactions for legal page

document.addEventListener("DOMContentLoaded", () => {
  // Optionally preview PDF inline or toggle sections if needed
  const toggleLinks = document.querySelectorAll(".legal-toggle");
  toggleLinks.forEach(link => {
    link.addEventListener("click", () => {
      const target = document.getElementById(link.dataset.target);
      if (target) {
        target.classList.toggle("hidden");
      }
    });
  });
});
