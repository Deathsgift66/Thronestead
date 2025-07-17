
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

export function applyTranslations(lang = 'en') {
  const translations = {
    en: {
      404_title: '404 - Page Not Found',
      404_msg: 'The page you requested could not be found.',
      home_link: 'Return to Home',
      sitemap_link: 'View Site Map',
      or_try: 'or try',
      search_link: 'searching',
      back_link: 'Go Back',
      nav_fail: '⚠️ Navigation failed to load. <a href="/" data-i18n="home_link">Return home</a>.',
      noscript_msg: 'JavaScript is disabled in your browser. Some features of Thronestead may not function correctly.'
    }
  };
  const strings = translations[lang];
  if (!strings) return;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const text = strings[key];
    if (!text) return;
    if (el.tagName === 'A') {
      el.textContent = text;
    } else {
      el.innerHTML = text;
    }
  });
}

