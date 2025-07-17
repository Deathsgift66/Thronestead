export function applyTranslations(lang = 'en') {
  const translations = {
    en: {
      404_title: '404 - Page Not Found',
      404_msg: 'The page you requested could not be found.',
      home_link: 'Return to Home',
      sitemap_link: 'View Site Map',
      or_try: 'or try',
      search_link: 'searching',
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
