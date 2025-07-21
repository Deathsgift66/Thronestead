
const fallbackTranslations = {
  en: {
    '404_title': '404 - Page Not Found',
    '404_msg': 'The page you requested could not be found.',
    home_link: 'Return to Home',
    sitemap_link: 'View Site Map',
    or_try: 'or try',
    search_link: 'searching',
    back_link: 'Go Back',
    nav_fail:
      '⚠️ Navigation failed to load. <a href="/" data-i18n="home_link">Return home</a>.',
    noscript_msg:
      'JavaScript is disabled in your browser. Some features of Thronestead may not function correctly.',
    '404_img_alt': 'Illustration of missing page',
    search_placeholder: 'Search...',
    go_button: 'Go'
  }
};

export function applyTranslations(lang = 'en') {
  const sets = window.translations || {};
  const strings = sets[lang] || sets.en || fallbackTranslations[lang] || fallbackTranslations.en;
  if (!strings) return;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const text = strings[key];
    if (!text) return;
    const tag = el.tagName.toLowerCase();
    if (tag === 'input' || tag === 'textarea') {
      el.placeholder = text;
    } else if (tag === 'a') {
      el.textContent = text;
    } else {
      el.innerHTML = text;
    }
  });
}

export function applyI18n() {
  const lang = document.documentElement.lang || 'en';
  applyTranslations(lang);
}

document.addEventListener('DOMContentLoaded', applyI18n);

