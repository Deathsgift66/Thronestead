export function applyI18n() {
  const lang = document.documentElement.lang || 'en';
  const sets = window.translations || {};
  const dict = sets[lang] || sets['en'];
  if (!dict) return;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    const text = dict[key];
    if (!text) return;
    const tag = el.tagName.toLowerCase();
    if (tag === 'input' || tag === 'textarea') {
      el.placeholder = text;
    } else {
      el.textContent = text;
    }
  });
}

document.addEventListener('DOMContentLoaded', applyI18n);
