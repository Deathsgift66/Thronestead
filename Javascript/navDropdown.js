/*
Project Name: Kingmakers Rise Frontend
File Name: navDropdown.js
Date: June 2, 2025
Author: Deathsgift66
*/
// navDropdown.js — Multi-dropdown sticky support
document.addEventListener("DOMContentLoaded", () => {
  const allDropdowns = document.querySelectorAll(".dropdown");

  allDropdowns.forEach((dropdown) => {
    const toggle = dropdown.querySelector(".dropdown-toggle");

    if (toggle) {
      toggle.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();

        allDropdowns.forEach((d) => {
          if (d !== dropdown) d.classList.remove("show");
        });

        dropdown.classList.toggle("show");
      });
    }
  });

  document.addEventListener("click", (e) => {
    allDropdowns.forEach((dropdown) => {
      if (!dropdown.contains(e.target)) {
        dropdown.classList.remove("show");
      }
    });
  });
});
