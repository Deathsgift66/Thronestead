// Project Name: Thronestead©
// File Name: 404.js
// Version:  7/16/2025
// Developer: Deathsgift66

import { applyTranslations } from '/Javascript/i18n.js';

const MAX_LEN = 255;
const ERROR_ID = (crypto.randomUUID && crypto.randomUUID()) || Date.now().toString();

function truncate(value) {
  if (typeof value !== 'string') return '';
  return value.length > MAX_LEN ? value.slice(0, MAX_LEN) : value;
}

function validate(payload) {
  if (typeof payload !== 'object') return false;
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
  for (const [key, type] of Object.entries(schema)) {
    const val = payload[key];
    if (val === undefined) return false;
    if (Array.isArray(type)) {
      if (!type.includes(typeof val)) return false;
    } else if (typeof val !== type) {
      return false;
    }
  }
  return true;
}

function schedule(cb) {
  if ('requestIdleCallback' in window) window.requestIdleCallback(cb);
  else setTimeout(cb, 2000);
}

function sendLog(payload) {
  if (!validate(payload)) return;
  schedule(() => {
    try {
      const data = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/logs/404', new Blob([data], { type: 'application/json' }));
      } else {
        fetch('/api/logs/404', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: data
        });
      }
    } catch (err) {
      if (import.meta.env.DEV) console.warn('Failed to log 404:', err);
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
    fetch('/api/log404', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: window.location.href })
    });
  } catch {}
}

async function init() {
  const theme = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.body.dataset.theme = theme;

  const userLang = navigator.language ? navigator.language.split('-')[0] : 'en';
  try {
    applyTranslations(userLang);
  } catch {
    applyTranslations('en');
  }

  const dynUrl = encodeURI(window.location.origin + window.location.pathname);
  const canonical = document.querySelector('link[rel="canonical"]');
  if (canonical) canonical.href = dynUrl;
  const og = document.getElementById('og-url');
  if (og) og.setAttribute('content', dynUrl);

  const struct = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'BreadcrumbList',
        'itemListElement': [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://www.thronestead.com/' },
          { '@type': 'ListItem', position: 2, name: '404', item: window.location.href }
        ]
      },
      {
        '@type': 'WebPage',
        'name': '404 Page',
        'description': 'Page not found on Thronestead.',
        'mainEntity': { '@type': 'WebPageElement', 'name': '404 Message', 'cssSelector': 'h1' }
      }
    ]
  };
  const sd = document.createElement('script');
  sd.type = 'application/ld+json';
  sd.textContent = JSON.stringify(struct);
  document.head.appendChild(sd);

  const backLink = document.getElementById('back-link');
  backLink?.addEventListener('click', e => {
    e.preventDefault();
    if (window.history.length > 1) {
      history.back();
    } else {
      window.location.href = '/';
    }
  });

  window.addEventListener('error', handleRuntimeError);

  let supabase = null;
  let supabaseReady = false;
  try {
    const mod = await import('/Javascript/supabaseClient.js');
    supabase = mod.supabase;
    supabaseReady = mod.supabaseReady;
  } catch {
    supabaseReady = false;
  }
  if (supabaseReady && supabase?.auth?.getUser) {
    let anonId = null;
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 3000);
      const { data: { user } } = await supabase.auth.getUser({ signal: ctrl.signal });
      clearTimeout(t);
      anonId = user?.id || null;
    } catch {}
    log404(anonId);
  } else {
    log404();
  }
}

document.addEventListener('DOMContentLoaded', init);
