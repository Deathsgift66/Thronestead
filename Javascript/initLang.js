export async function initLang() {
  const lang = document.documentElement.lang || 'en';
  const sets = window.translations || {};
  if (!sets[lang]) {
    try {
      const res = await fetch(`/translations/${lang}.json`);
      if (res.ok) {
        const data = await res.json();
        sets[lang] = data;
        window.translations = sets;
      }
    } catch (err) {
      console.warn('Failed to load translations', err);
    }
  }
  const { applyI18n } = await import('/Javascript/i18n.js');
  applyI18n();
}

document.addEventListener('DOMContentLoaded', initLang);
