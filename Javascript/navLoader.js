// Project Name: Thronestead©
// File Name: navLoader.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
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
      if (fallback) fallback.hidden = true;

      // Lazy-load all navbar-related interactive scripts in parallel
      const modules = await Promise.allSettled([
        import("./navDropdown.js"),
        import("./navbar.js"),
        import("./mobileLinkBar.js"),
        import("./notificationBell.js"),
        import("./logout.js"),
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
          <p>⚠️ Navigation failed to load. <a href="index.html">Return home</a>.</p>
        </div>
      `;
    }
  }

  loadNavbar();
});
