/*
Project Name: Kingmakers Rise Frontend
File Name: navLoader.js
Date: June 2, 2025
Author: Deathsgift66
Updated: June 13, 2025
Enhancements:
- Error fallback and retry support
- Defensive DOM targeting
- Parallel async module injection
- Initialization confirmation logging
- Resilient loading for offline/dev states
- Modular future expansion via plugin hook
*/

document.addEventListener("DOMContentLoaded", () => {
  const NAVBAR_PATH = "/navbar.html";
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

      // Lazy-load all navbar-related interactive scripts in parallel
      const modules = await Promise.allSettled([
        import("./navDropdown.js"),
        import("./navbar.js"),
        import("./mobileLinkBar.js"),
        import("./notificationBell.js"),
        // Future expansion hook
        // import("./navPlugins.js")
      ]);

      modules.forEach((m, i) => {
        if (m.status === "rejected") {
          console.warn(`Module ${i} failed:`, m.reason);
        }
      });

      console.info("✅ Navbar successfully injected and initialized.");

    } catch (err) {
      console.error("❌ Navbar injection failed:", err);
      target.innerHTML = `
        <div class="navbar-failover">
          <p>⚠️ Navigation failed to load. <a href="/">Return home</a>.</p>
        </div>
      `;
    }
  }

  loadNavbar();
});
