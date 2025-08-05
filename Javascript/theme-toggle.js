export function initThemeToggle() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;

  const saved =
    localStorage.getItem('theme') || document.body.getAttribute('data-theme') || 'parchment';
  document.body.setAttribute('data-theme', saved);

  function update(state) {
    const theme = state || document.body.getAttribute('data-theme');
    btn.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    btn.setAttribute('aria-pressed', theme === 'dark');
    btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  }

  update(saved);
  btn.addEventListener('click', () => {
    const current = document.body.getAttribute('data-theme') === 'dark' ? 'parchment' : 'dark';
    document.body.setAttribute('data-theme', current);
    localStorage.setItem('theme', current);
    update(current);
  });
}

if (document.readyState !== 'loading') {
  initThemeToggle();
} else {
  document.addEventListener('DOMContentLoaded', initThemeToggle);
}
