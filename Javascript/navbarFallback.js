// Shows fallback navigation if navLoader.js fails or doesn't populate
function injectFallback() {
  const container = document.getElementById('navbar-container');
  const tpl = document.getElementById('nav-fallback');
  if (container && tpl && container.children.length === 0) {
    container.appendChild(tpl.content.cloneNode(true));
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const navScript = document.getElementById('navLoaderScript');
  if (navScript) {
    navScript.addEventListener('error', injectFallback, { once: true });
  }

  if (typeof window.navLoader === 'undefined') {
    // Fallback in case navLoader fails silently
    setTimeout(injectFallback, 4000);
  }
});
