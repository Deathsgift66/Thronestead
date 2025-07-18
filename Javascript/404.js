// Project Name: Thronestead©
// File Name: 404.js
// Version: 7/18/2025
// Developer: Deathsgift66

import { applyTranslations } from '/Javascript/i18n.js';

const MAX_LEN = 255;
const ERROR_ID = crypto.randomUUID?.() || Date.now().toString();

function truncate(str) {
  return typeof str === 'string' && str.length > MAX_LEN ? str.slice(0, MAX_LEN) : str || '';
}

function schedule(fn) {
  if ('requestIdleCallback' in window) requestIdleCallback(fn);
  else setTimeout(fn, 2000);
}

function validate(payload) {
  const schema = {
    path: 'string',
    search: 'string',
    referrer: 'string',
    user_agent: 'string',
    type: 'string',
    anon_id: ['string', 'object'],
    timestamp: 'number',
    error_id: 'string'
  };
  return Object.entries(schema).every(([k, type]) => {
    const val = payload[k];
    if (val === undefined) return false;
    return Array.isArray(type) ? type.includes(typeof val) : typeof val === type;
  });
}

function sendLog(payload) {
  if (!validate(payload)) return;
  schedule(() => {
    try {
      const json = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/logs/404', new Blob([json], { type: 'application/json' }));
      } else {
        fetch('/api/logs/404', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: json
        });
      }
    } catch (err) {
      if (import.meta?.env?.DEV) console.warn('404 log failed:', err);
    }
  });
}

function handleRuntimeError(e) {
  sendLog({
    path: truncate(location.pathname),
    search: truncate(location.search),
    referrer: truncate(document.referrer),
    user_agent: truncate(navigator.userAgent),
    type: 'runtime',
    anon_id: null,
    timestamp: Date.now(),
    error_id: ERROR_ID,
    message: truncate(e.message || '')
  });
}

async function log404(anonId = null) {
  const payload = {
    path: truncate(location.pathname),
    search: truncate(location.search),
    referrer: truncate(document.referrer),
    user_agent: truncate(navigator.userAgent),
    type: '404',
    anon_id: anonId,
    timestamp: Date.now(),
    error_id: ERROR_ID
  };
  sendLog(payload);

  try {
    fetch('/api/log/404', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: location.href })
    });
  } catch {
    /* Silent fallback */
  }
}

async function checkSearchAvailability() {
  try {
    const res = await fetch('/search.html', { method: 'HEAD' });
    if (!res.ok) throw new Error('Search not OK');
  } catch {
    const form = document.querySelector('form[action="/search.html"]');
    if (form) {
      const alert = document.createElement('div');
      alert.setAttribute('role', 'alert');
      alert.textContent = 'Search is currently unavailable.';
      form.before(alert);
      form.remove();
    }
  }
}

function injectStructuredData() {
  const struct = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://www.thronestead.com/' },
          { '@type': 'ListItem', position: 2, name: '404', item: location.href }
        ]
      },
      {
        '@type': 'WebPage',
        name: '404 Page',
        description: 'Page not found on Thronestead.',
        mainEntity: { '@type': 'WebPageElement', name: '404 Message', cssSelector: 'h1' }
      }
    ]
  };
  const script = document.createElement('script');
  script.type = 'application/ld+json';
  script.textContent = JSON.stringify(struct);
  document.head.appendChild(script);
}

function updateMetaUrls() {
  const canonical = document.querySelector('link[rel="canonical"]');
  const ogUrl = document.querySelector('meta[property="og:url"]');
  const fullUrl = encodeURI(location.origin + location.pathname);

  if (canonical) canonical.href = fullUrl;
  if (ogUrl) ogUrl.setAttribute('content', fullUrl);
}

function initBackLink() {
  const backLink = document.getElementById('back-link');
  if (!backLink) return;

  backLink.addEventListener('click', e => {
    e.preventDefault();
    if (history.length > 1) {
      history.back();
    } else {
      location.href = '/';
    }
  });
}

async function detectUserAndLog404() {
  let supabase, supabaseReady = false;
  try {
    const mod = await import('/Javascript/supabaseClient.js');
    supabase = mod.supabase;
    supabaseReady = mod.supabaseReady;
  } catch {
    return log404();
  }

  if (!supabaseReady || !supabase?.auth?.getUser) return log404();

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const { data: { user } } = await supabase.auth.getUser({ signal: controller.signal });
    clearTimeout(timeout);
    log404(user?.id || null);
  } catch {
    log404();
  }
}

function navFallback() {
  const nav = document.getElementById('navbar-container');
  if (!nav || nav.querySelector('nav') || nav.querySelector('.navbar-failover')) return;

  const tpl = document.getElementById('nav-fallback');
  if (tpl?.content) {
    nav.replaceChildren(tpl.content.cloneNode(true));
  } else {
    nav.innerHTML = '<div class="navbar-failover">⚠️ Navigation unavailable. <a href="/">Home</a>.</div>';
  }
}

function onReady() {
  const theme = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.body.dataset.theme = theme;

  const lang = navigator.language?.split('-')[0] || 'en';
  try {
    applyTranslations(lang);
  } catch {
    applyTranslations('en');
  }

  updateMetaUrls();
  injectStructuredData();
  checkSearchAvailability();
  initBackLink();

  const navScript = document.getElementById('navLoaderScript');
  navScript?.addEventListener('error', navFallback);

  if (typeof window.navLoader === 'undefined') {
    setTimeout(navFallback, 4000);
  }

  window.addEventListener('error', handleRuntimeError);
  detectUserAndLog404();
}

document.addEventListener('DOMContentLoaded', onReady);
