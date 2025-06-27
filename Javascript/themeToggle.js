/*
export function initThemeToggle() {
  const btn = document.getElementById('theme-toggle');
  const saved = localStorage.getItem('theme') || 'parchment';
  document.body.setAttribute('data-theme', saved);
  if (!btn) return;

  function update() {
    const theme = document.body.getAttribute('data-theme');
    btn.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
  }

  update();
  btn.addEventListener('click', () => {
    const current = document.body.getAttribute('data-theme') === 'dark' ? 'parchment' : 'dark';
    document.body.setAttribute('data-theme', current);
    localStorage.setItem('theme', current);
    update();
  });
}

if (document.readyState !== 'loading') {
  initThemeToggle();
} else {
  document.addEventListener('DOMContentLoaded', initThemeToggle);
}
*/
