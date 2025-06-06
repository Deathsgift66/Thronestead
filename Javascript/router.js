// Simple client-side router for single-page navigation
export function initRouter() {
  document.body.addEventListener('click', async (e) => {
    const target = e.target.closest('a');
    if (!target) return;
    const href = target.getAttribute('href');
    if (href && !href.startsWith('http') && !href.startsWith('#')) {
      e.preventDefault();
      await navigate(href);
    }
  });

  const initialPath = window.location.pathname.replace(/^\//, '') || 'index.html';
  navigate(initialPath);
}

export async function navigate(path) {
  const container = document.getElementById('app');
  if (!container) {
    window.location.href = path;
    return;
  }
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error('Network response was not ok');
    container.innerHTML = await res.text();
    window.history.pushState({}, '', path);
  } catch (err) {
    const res = await fetch('404.html');
    container.innerHTML = await res.text();
    window.history.pushState({}, '', path);
  }
}
