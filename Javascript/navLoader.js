/*
Project Name: Kingmakers Rise Frontend
File Name: navLoader.js
Date: June 2, 2025
Author: Deathsgift66
*/
// navLoader.js — Dynamically injects shared navbar
document.addEventListener("DOMContentLoaded", async () => {
  const target =
    document.getElementById("kr-navbar-container") ||
    document.getElementById("navbar-container");

  if (target) {
    const response = await fetch("navbar.html");
    const html = await response.text();
    target.innerHTML = html;

    // Re-init dropdown logic and profile loader in parallel
    await Promise.all([
      import("./navDropdown.js"),
      import("./navbar.js"),
      import("./mobileLinkBar.js"),
      import("./notificationBell.js"),
    ]);
  }
});
