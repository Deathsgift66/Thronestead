export async function initLang() {
  const lang = document.documentElement.lang || 'en';
  if (!window.translations) {
    try {
      const res = await fetch(`/translations/${lang}.json`);
      if (res.ok) {
        const data = await res.json();
        window.translations = { [lang]: data };
      }
    } catch (err) {
      console.warn('Failed to load translations', err);
    }
  }
  const { applyTranslations } = await import('/Javascript/i18n.js');
  applyTranslations(lang);
}

document.addEventListener('DOMContentLoaded', initLang);
