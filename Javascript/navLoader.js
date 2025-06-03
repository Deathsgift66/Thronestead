// navLoader.js — Dynamically injects shared navbar
document.addEventListener("DOMContentLoaded", async () => {
  const target = document.getElementById("kr-navbar-container");

  if (target) {
    const response = await fetch("../shared/navbar.html");
    const html = await response.text();
    target.innerHTML = html;

    // Re-init dropdown logic
    import("./navDropdown.js");
  }
});
