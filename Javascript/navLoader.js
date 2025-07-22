// Project Name: Thronestead©
// File Name: navLoader.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
window.navLoader = true;
document.addEventListener("DOMContentLoaded", () => {
  // Fetch navbar relative to the current page so deployment under a subpath
  // still resolves correctly
  // Resolve navbar path relative to this script so deployments under a subpath
  // (e.g. example.com/thronestead/) still locate the correct file
  // Load the shared navbar fragment from the public directory so it works
  // across deployments that serve the site from a subpath.
  const NAVBAR_PATH = new URL("../public/navbar.html", import.meta.url).pathname;
  const MAX_RETRIES = 3;
  const RETRY_DELAY_MS = 500;
  const target =
    document.getElementById("kr-navbar-container") ||
    document.getElementById("navbar-container");

  if (!target) {
    console.warn("⚠️ Navbar container not found. Skipping injection.");
    return;
  }

  // Utility: Retry fetch wrapper with delay
  async function fetchWithRetry(url, retries = MAX_RETRIES) {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.text();
      } catch (err) {
        console.warn(`Attempt ${attempt} failed: ${err.message}`);
        if (attempt < retries) await new Promise(res => setTimeout(res, RETRY_DELAY_MS));
      }
    }
    throw new Error("Failed to fetch navbar after max retries.");
  }

  // Inject navbar HTML and initialize related JS
  async function loadNavbar() {
    try {
      const html = await fetchWithRetry(NAVBAR_PATH);
      target.innerHTML = html;
      const currentPage = window.location.pathname.split("/").pop() || "index.html";
      const currentLink = target.querySelector(`a[href="${currentPage}"]`);
      if (currentLink) currentLink.setAttribute("aria-current", "page");
      const fallback = document.getElementById("nav-fallback");
      if (fallback && fallback.tagName !== "TEMPLATE") fallback.hidden = true;

      // Lazy-load consolidated navbar functionality
      try {
        await import("./navbarBundle.js");
      } catch (err) {
        console.warn("Navbar bundle failed:", err);
      }

      console.info("✅ Navbar successfully injected and initialized.");

    } catch (err) {
      console.error("❌ Navbar injection failed:", err);
      const tpl = document.getElementById("nav-fallback");
      if (tpl && tpl.content) {
        target.appendChild(tpl.content.cloneNode(true));
      } else {
        target.innerHTML = `
          <div class="navbar-failover">
            <p>⚠️ Navigation failed to load. <a href="index.html">Return home</a>.</p>
          </div>
        `;
      }
    }
  }

  loadNavbar();
});
