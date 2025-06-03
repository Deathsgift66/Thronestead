// legal.js - Handles loading and dynamic interactions for legal page

document.addEventListener("DOMContentLoaded", () => {
  console.log("Legal page loaded.");
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
