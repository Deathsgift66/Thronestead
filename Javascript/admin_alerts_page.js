// Extracted from admin_alerts.html inline script, version 7.1.2025.10.38

import { supabase } from '/Javascript/supabaseClient.js';
import {
  authJsonFetch,
  showToast,
  debounce,
  getCsrfToken,
  openModal,
  closeModal
} from '/Javascript/utils.js';
import { setupReauthButtons } from '/Javascript/reauth.js';
import { validateSessionOrLogout } from '/Javascript/auth.js';

window.requireAdmin = true;

window.addEventListener('error', e => {
  console.error('Unhandled error:', e.error || e.message);
  showToast('Unexpected error occurred', 'error');
});
window.addEventListener('unhandledrejection', e => {
  console.error('Unhandled promise rejection:', e.reason);
  showToast('Unexpected error occurred', 'error');
});

const REFRESH_MS = 30000;
const AUTO_EXPIRE_MS = 60000;
const MAX_FEED_ITEMS = 250;
const FILTER_KEYS = ['start', 'end', 'type', 'severity', 'kingdom', 'alliance'];
const API_ENDPOINTS = {
  flag: '/api/admin/flag',
  freeze: '/api/admin/freeze',
  ban: '/api/admin/ban',
  dismiss: '/api/admin/dismiss_alert',
  flag_ip: '/api/admin/flag_ip',
  suspend_user: '/api/admin/suspend_user',
  mark_alert_handled: '/api/admin/mark_alert_handled'
};
let realtimeSub = null;
let currentData = null;
let lastTimestamp = null;
const buttonCooldownSet = new Set();
let exportLock = false;
let userScrolling = false;
let csrfToken = getCsrfToken();

function setRealtimeStatus(text) {
  const el = document.getElementById('realtime-status');
  if (el) el.textContent = text;
}

async function refreshCsrf() {
  csrfToken = getCsrfToken();
  try {
    await fetch('/api/admin/csrf', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      referrerPolicy: 'strict-origin-when-cross-origin',
      body: JSON.stringify({ token: csrfToken })
    });
  } catch (err) {
    console.warn('Failed to sync CSRF token', err);
  }
}

function scheduleCsrfRefresh() {
  setTimeout(async () => {
    await refreshCsrf();
    scheduleCsrfRefresh();
  }, 15 * 60 * 1000);
}

const debouncedLoad = debounce(loadAlerts, 400);

function initTabs() {
  const container = document.querySelector('.alert-tabs');
  if (!container) return;
  container.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => selectTab(tab));
  });
  container.addEventListener('keydown', e => {
    const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End'];
    if (!keys.includes(e.key)) return;
    const tabs = Array.from(container.querySelectorAll('.tab'));
    let idx = tabs.indexOf(document.activeElement);
    if (idx === -1) idx = 0;
    if (e.key === 'ArrowRight') idx = (idx + 1) % tabs.length;
    if (e.key === 'ArrowLeft') idx = (idx - 1 + tabs.length) % tabs.length;
    if (e.key === 'Home') idx = 0;
    if (e.key === 'End') idx = tabs.length - 1;
    tabs[idx].focus();
    e.preventDefault();
  });
}

function initPage() {
  initTabs();
  const params = new URLSearchParams(window.location.search);
  const savedType = localStorage.getItem('admin-alert-tab');
  const type = params.get('type') || savedType;
  const tab = type ? document.querySelector(`.tab[data-type="${type}"]`) : null;
  if (tab) tab.click();
  else loadAlerts();
  setTimeout(() => { if (!document.hidden) loadAlerts(); }, REFRESH_MS);
  scheduleCsrfRefresh();
  subscribeToRealtime();
  document.getElementById('refresh-alerts')?.addEventListener('click', () => {
    const btn = document.getElementById('refresh-alerts');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="loading-spinner"></span> Refreshing...';
    }
    loadAlerts().finally(() => {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Refresh';
      }
    });
  });
  document.getElementById('clear-filters')?.addEventListener('click', () => {
    const btn = document.getElementById('clear-filters');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="loading-spinner"></span> Clearing...';
    }
    clearFilters();
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Clear';
    }
  });
  document.getElementById('export-csv')?.addEventListener('click', exportCSV);
  document.getElementById('export-json')?.addEventListener('click', exportJSON);
  const feed = document.querySelector('[role="tabpanel"]');
  if (!feed) {
    console.warn('alerts-feed container missing');
  } else {
    feed.addEventListener('click', handleActionClick);
    feed.addEventListener('keydown', e => {
      if (!e.target.classList.contains('action-btn')) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleActionClick({ target: e.target });
      }
    });
    feed.addEventListener('scroll', () => {
      userScrolling = feed.scrollTop + feed.clientHeight < feed.scrollHeight - 5;
    });
  }
  document.querySelectorAll('.filter-input').forEach(el => {
    const ev = el.tagName === 'SELECT' ? 'change' : 'input';
    el.addEventListener(ev, () => {
      lastTimestamp = null;
      debouncedLoad();
      subscribeToRealtime();
    });
  });
  document.getElementById('load-more-alerts')?.addEventListener('click', () => loadAlerts(true));
  initThemeToggle();
  setupReauthButtons('.action-btn');
  supabase.auth.onAuthStateChange((evt, session) => {
    try {
      if (!session) validateSessionOrLogout();
      if (evt === 'SIGNED_IN' || evt === 'SIGNED_OUT') refreshCsrf();
    } catch (err) {
      console.error('Auth state handler failed', err);
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  requestAnimationFrame(() => {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(initPage);
    } else {
      setTimeout(initPage, 200);
    }
  });
});

window.addEventListener('beforeunload', async () => {
  if (realtimeSub) {
    await realtimeSub.unsubscribe();
    realtimeSub = null;
  }
  setRealtimeStatus('Disconnected: ❌');
});

async function subscribeToRealtime() {
  if (realtimeSub) {
    try {
      await realtimeSub.unsubscribe();
    } catch (err) {
      console.warn('Failed to unsubscribe realtime', err);
    }
    realtimeSub = null;
  }
  setRealtimeStatus('Connecting...');
  const { kingdom, alliance } = getFilters();
  const opts = { event: 'INSERT', schema: 'public', table: 'admin_alerts' };
  const channel = supabase.channel('admin_alerts');
  if (kingdom) channel.on('postgres_changes', { ...opts, filter: `kingdom_id=eq.${kingdom}` }, debouncedLoad);
  if (alliance) channel.on('postgres_changes', { ...opts, filter: `alliance_id=eq.${alliance}` }, debouncedLoad);
  if (!kingdom && !alliance) channel.on('postgres_changes', opts, debouncedLoad);
  realtimeSub = channel.subscribe()
    .then(() => setRealtimeStatus('Live: ✅'))
    .catch(err => {
      console.error('Realtime subscribe failed', err);
      setRealtimeStatus('Disconnected: ❌');
      showToast('Realtime connection failed', 'error');
      if (navigator.onLine) setTimeout(subscribeToRealtime, 5000);
    });
}

async function loadAlerts(append = false) {
  const container = document.querySelector('[role="tabpanel"]');
  if (!container) {
    console.warn('alerts-feed container missing');
    return;
  }
  const moreBtn = document.getElementById('load-more-alerts');
  if (append && moreBtn) {
    moreBtn.disabled = true;
    moreBtn.dataset.origText = moreBtn.textContent;
    moreBtn.innerHTML = '<span class="loading-spinner"></span> Loading...';
  }
  if (!append) {
    container.innerHTML = '<p><span class="loading-spinner" aria-hidden="true"></span> Loading alerts...</p>';
    lastTimestamp = null;
  }

  try {
    const filters = getFilters();
    if (append && lastTimestamp) filters.end = lastTimestamp;
    const data = await authJsonFetch('/api/admin/alerts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      referrerPolicy: 'strict-origin-when-cross-origin',
      body: JSON.stringify(filters)
    });
    if (append && currentData && Array.isArray(currentData.alerts)) {
      currentData.alerts = currentData.alerts.concat(data.alerts || []);
    } else {
      currentData = data;
      container.innerHTML = '';
    }

    const renderSet = Array.isArray(data.alerts)
      ? [{ title: 'Alerts', items: data.alerts }]
      : [
          { title: 'Moderation', items: data.moderation_notes },
          { title: 'War', items: data.recent_war_logs },
          { title: 'Diplomacy', items: data.treaty_activity },
          { title: 'Audit Log', items: data.audit },
          { title: 'Admin Actions', items: data.admin_actions }
        ];

    if (!renderSet.some(s => (s.items || []).length)) {
      container.innerHTML = '<p>No alerts found.</p>';
      return;
    }

    let remaining = MAX_FEED_ITEMS;
    renderSet.forEach(set => {
      if (!remaining) {
        set.items = [];
        return;
      }
      set.items = (set.items || []).slice(0, remaining);
      remaining -= set.items.length;
    });
    if (remaining <= 0) {
      showToast('⚠ Only first 250 alerts shown. Refine filters.', 'warning');
    }

    lastTimestamp = data.alerts?.[data.alerts.length - 1]?.timestamp || null;
    if (data.alerts && data.alerts.length >= 100) {
      moreBtn?.classList.remove('hidden');
    } else {
      moreBtn?.classList.add('hidden');
    }

    renderSet.forEach(({ title, items }) => renderCategory(container, title, items));
    const count = renderSet.reduce((n, s) => n + (s.items ? s.items.length : 0), 0);
    const countEl = document.getElementById('alert-count');
    if (countEl) countEl.textContent = `${count} alerts shown`;
    if (!userScrolling) container.scrollTop = container.scrollHeight;
  } catch (err) {
    console.error('❌ Failed to load alerts:', err);
    const msg = escapeHTML(err.message || 'Unknown error');
    container.innerHTML = `<p>Error loading alerts: ${msg}. Please try again later.</p>`;
    showToast(`❌ Failed to load alerts: ${msg}`, 'error');
  } finally {
    if (moreBtn) {
      moreBtn.disabled = false;
      if (append) moreBtn.textContent = moreBtn.dataset.origText || 'Load More';
    }
  }
}

function renderCategory(container, title, items = []) {
  if (!items.length) return;

  const section = document.createElement('div');
  section.className = 'alert-category';
  section.setAttribute('role', 'region');
  section.setAttribute('aria-label', title);

  const header = document.createElement('h3');
  header.textContent = title;
  section.appendChild(header);

  items.forEach(item => {
    const div = document.createElement('div');
    div.className = `alert-item ${mapSeverity(item.severity || item.priority)}`;
    div.setAttribute('role', 'article');
    const evType = escapeHTML((item.event_type || item.type || 'log').toUpperCase());
    div.innerHTML = `
      <strong>[${evType}]</strong>
      <p>${formatItem(item)}</p>
      <small>
         Kingdom: ${escapeHTML(String(item.kingdom_id || '—'))} |
         Alliance: ${escapeHTML(String(item.alliance_id || '—'))} |
         ${item.timestamp ? formatTime(item.timestamp) : '—'}
      </small>
    `;

    const actions = document.createElement('div');
    actions.className = 'action-buttons';
    const actionMap = [
      { action: 'flag', label: 'Flag', data: { player_id: item.player_id } },
      { action: 'freeze', label: 'Freeze', data: { player_id: item.player_id } },
      { action: 'ban', label: 'Ban', data: { player_id: item.player_id } },
      { action: 'dismiss', label: 'Dismiss', data: { alert_id: getAlertId(item) } },
      { action: 'flag_ip', label: 'Flag IP', data: { ip: item.ip } },
      { action: 'suspend_user', label: 'Suspend', data: { user_id: item.user_id } },
      { action: 'mark_alert_handled', label: 'Mark Reviewed', data: { alert_id: getAlertId(item) } }
    ];

    actionMap.forEach(({ action, label, data }) => {
      const hasValidData = Object.values(data).some(v => v !== undefined && v !== null && v !== '');
      if (!hasValidData) return;
      const btn = document.createElement('button');
      btn.className = 'btn btn-small action-btn';
      btn.textContent = label;
      btn.dataset.action = action;
      Object.entries(data).forEach(([k, v]) => (btn.dataset[k] = v));
      const target = data.player_id || data.user_id || data.alert_id || data.ip || '';
      let aria = label;
      if (action === 'dismiss' || action === 'mark_alert_handled') aria += ` alert ${target}`;
      else if (action === 'flag_ip') aria += ` IP ${target}`;
      else aria += ` user ${target}`;
      btn.setAttribute('aria-label', aria.trim());
      actions.appendChild(btn);
    });

    div.appendChild(actions);
    setTimeout(() => div.classList.add('expired'), AUTO_EXPIRE_MS);
    section.appendChild(div);
  });

  container.appendChild(section);
}

let pendingAction = null;

async function handleActionClick(e) {
  if (!e.target.classList.contains('action-btn')) return;
  const btn = e.target;
  const action = btn.dataset.action;
  const key = `${action}:${btn.dataset.alert_id || btn.dataset.player_id || btn.dataset.user_id || btn.dataset.ip || ''}`;
  if (buttonCooldownSet.has(key)) return;
  buttonCooldownSet.add(key);

  const idPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const ipPattern = /^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$/;

  const requiresConfirm = ['ban', 'freeze', 'suspend_user'];
  if (requiresConfirm.includes(action)) {
    pendingAction = () => performAction(btn, action, idPattern, ipPattern);
    openModal('confirm-modal');
    return;
  }
  await performAction(btn, action, idPattern, ipPattern);
}

async function performAction(btn, action, idPattern, ipPattern) {
  btn.disabled = true;
  let success = false;
  try {
    switch (action) {
      case 'flag':
        if (!idPattern.test(btn.dataset.player_id)) {
          console.error('Invalid player id:', btn.dataset.player_id);
          throw new Error('Invalid player id');
        }
        await postAdminAction(API_ENDPOINTS.flag, { player_id: btn.dataset.player_id, alert_id: btn.dataset.alert_id });
        success = true;
        break;
      case 'freeze':
        if (!idPattern.test(btn.dataset.player_id)) {
          console.error('Invalid player id:', btn.dataset.player_id);
          throw new Error('Invalid player id');
        }
        await postAdminAction(API_ENDPOINTS.freeze, { player_id: btn.dataset.player_id, alert_id: btn.dataset.alert_id });
        success = true;
        break;
      case 'ban':
        if (!idPattern.test(btn.dataset.player_id)) {
          console.error('Invalid player id:', btn.dataset.player_id);
          throw new Error('Invalid player id');
        }
        await postAdminAction(API_ENDPOINTS.ban, { player_id: btn.dataset.player_id, alert_id: btn.dataset.alert_id });
        success = true;
        break;
      case 'dismiss':
        if (!idPattern.test(btn.dataset.alert_id)) {
          console.error('Invalid alert id:', btn.dataset.alert_id);
          throw new Error('Invalid alert id');
        }
        await postAdminAction(API_ENDPOINTS.dismiss, { alert_id: btn.dataset.alert_id });
        success = true;
        break;
      case 'flag_ip':
        if (!ipPattern.test(btn.dataset.ip)) {
          console.error('Invalid IP:', btn.dataset.ip);
          throw new Error('Invalid IP');
        }
        await postAdminAction(API_ENDPOINTS.flag_ip, { ip: btn.dataset.ip });
        success = true;
        break;
      case 'suspend_user':
        if (!idPattern.test(btn.dataset.user_id)) {
          console.error('Invalid user id:', btn.dataset.user_id);
          throw new Error('Invalid user id');
        }
        await postAdminAction(API_ENDPOINTS.suspend_user, { user_id: btn.dataset.user_id });
        success = true;
        break;
      case 'mark_alert_handled':
        await postAdminAction(API_ENDPOINTS.mark_alert_handled, { alert_id: btn.dataset.alert_id });
        btn.disabled = true;
        success = true;
        break;
    }

    showToast(`✅ ${action.replace(/_/g, ' ')} successful.`, 'success');
    if (btn.dataset.alert_id) {
      const item = btn.closest('.alert-item');
      if (item) item.remove();
    }
  } catch (err) {
    console.error(`❌ Action [${action}] failed:`, err);
    const msg = escapeHTML(err.message || 'Unknown error');
    const level = msg.toLowerCase().includes('invalid') ? 'warning' : 'error';
    showToast(`❌ ${action} failed: ${msg}`, level);
  } finally {
    if (success) {
      buttonCooldownSet.delete(key);
    } else {
      setTimeout(() => {
        buttonCooldownSet.delete(key);
        btn.disabled = false;
      }, 3000);
    }
  }
}

document.getElementById('confirm-yes')?.addEventListener('click', async () => {
  closeModal('confirm-modal');
  if (typeof pendingAction === 'function') await pendingAction();
  pendingAction = null;
});
document.getElementById('confirm-no')?.addEventListener('click', () => {
  pendingAction = null;
  closeModal('confirm-modal');
});

async function postAdminAction(endpoint, payload) {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.access_token) throw new Error('Session missing. Reauthenticate.');
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${session.access_token}`,
    'X-CSRF-Token': csrfToken
  };
  const res = await fetch(endpoint, {
    method: 'POST',
    credentials: 'include',
    headers,
    referrerPolicy: 'strict-origin-when-cross-origin',
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    console.error('Admin action failed with status', res.status);
    let msg = await res.text();
    if (res.status === 401) msg = 'Unauthorized. Please reauthenticate.';
    if (res.status === 403) msg = 'Access denied.';
    if (res.status === 0) msg = 'Network error or CORS blocked.';
    throw new Error(msg);
  }
}

function toUTC(val) {
  if (!val) return '';
  const d = new Date(val);
  return isNaN(d) ? '' : d.toISOString();
}

function getFilters() {
  const entries = FILTER_KEYS
    .map(k => {
      let v = document.getElementById(`filter-${k}`)?.value;
      if ((k === 'start' || k === 'end') && v) v = toUTC(v);
      return [k, v];
    })
    .filter(([, v]) => v);
  return sanitizeFilters(Object.fromEntries(entries));
}

function sanitizeFilters(obj) {
  const idPattern = /^[a-zA-Z0-9_-]{1,40}$/;
  const types = ['moderation','war','economy','diplomacy','quests','abuse','spy','vip'];
  const severities = ['low','medium','high'];
  if (obj.kingdom && !idPattern.test(obj.kingdom)) delete obj.kingdom;
  if (obj.alliance && !idPattern.test(obj.alliance)) delete obj.alliance;
  if (obj.type && !types.includes(obj.type)) delete obj.type;
  if (obj.severity && !severities.includes(obj.severity)) delete obj.severity;
  if (obj.start && Number.isNaN(Date.parse(obj.start))) delete obj.start;
  if (obj.end && Number.isNaN(Date.parse(obj.end))) delete obj.end;
  return obj;
}

function clearFilters() {
  document.querySelectorAll('.filter-input').forEach(el => (el.value = ''));
  lastTimestamp = null;
  loadAlerts();
  subscribeToRealtime();
}

function mapSeverity(sev = '') {
  if (typeof sev !== 'string') {
    console.warn('Unexpected severity value', sev);
    return 'severity-low';
  }
  const s = sev.toLowerCase();
  if (['high', 'critical'].includes(s)) return 'severity-high';
  if (s === 'medium') return 'severity-medium';
  if (s === 'low') return 'severity-low';
  console.warn('Unknown severity level:', sev);
  return 'severity-low';
}

function escapeHTML(str = '') {
  if (typeof str !== 'string') {
    console.error('escapeHTML expected string but received', str);
    return '';
  }
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatItem(item) {
  const base = item.message || `${item.action || ''} - ${item.details || item.note || 'No details'}`;
  return escapeHTML(base);
}

function formatTime(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  const diff = Date.now() - d.getTime();
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
  const minutes = Math.round(diff / 60000);
  let rel;
  if (Math.abs(minutes) < 60) {
    rel = rtf.format(-minutes, 'minute');
  } else {
    const hours = Math.round(diff / 3600000);
    if (Math.abs(hours) < 24) rel = rtf.format(-hours, 'hour');
    else rel = rtf.format(-Math.round(diff / 86400000), 'day');
  }
  return `${d.toLocaleString()} (${rel})`;
}

function getAlertId(item) {
  if (!item.alert_id) {
    if (item.id) {
      console.warn('Missing alert_id, using fallback id:', item.id);
      return item.id;
    }
    console.warn('Missing alert_id and fallback id:', item);
    return '';
  }
  return item.alert_id;
}

function exportJSON() {
  if (exportLock) return;
  if (!currentData || (currentData.alerts || []).length === 0) {
    showToast('No data to export.', 'info');
    return;
  }
  const btn = document.getElementById('export-json');
  const origText = btn ? btn.textContent : '';
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Loading...';
  }
  exportLock = true;
  if ((currentData.alerts || []).length > MAX_FEED_ITEMS) {
    showToast(`⚠ Exporting more than ${MAX_FEED_ITEMS} items may be slow.`, 'warning');
  }
  const blob = new Blob([JSON.stringify(currentData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'alerts.json';
  a.click();
  URL.revokeObjectURL(url);
  if (btn) {
    btn.disabled = false;
    btn.textContent = origText;
  }
  exportLock = false;
  document.getElementById('export-status').textContent = 'JSON export complete.';
}

function exportCSV() {
  if (exportLock) return;
  if (!currentData || !(Array.isArray(currentData.alerts)) || currentData.alerts.length === 0) {
    showToast('No data to export.', 'info');
    return;
  }
  const btn = document.getElementById('export-csv');
  const origText = btn ? btn.textContent : '';
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Loading...';
  }
  exportLock = true;
  if (currentData.alerts.length > MAX_FEED_ITEMS) {
    showToast(`⚠ Exporting more than ${MAX_FEED_ITEMS} items may be slow.`, 'warning');
  }
  const sanitize = v => `"${String(v).replace(/"/g, '""')}"`;
  const rows = [
    ['type', 'message', 'kingdom', 'alliance', 'timestamp', 'severity'].map(sanitize)
  ];
  currentData.alerts.forEach(it => {
    rows.push([
      sanitize(it.event_type || it.type || ''),
      sanitize(it.message || it.note || ''),
      sanitize(it.kingdom_id || ''),
      sanitize(it.alliance_id || ''),
      sanitize(it.timestamp || ''),
      sanitize(it.severity || it.priority || '')
    ]);
  });
  const csv = rows.map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'alerts.csv';
  a.click();
  URL.revokeObjectURL(url);
  if (btn) {
    btn.disabled = false;
    btn.textContent = origText;
  }
  exportLock = false;
  document.getElementById('export-status').textContent = 'CSV export complete.';
}

function selectTab(tab) {
  document.querySelectorAll('.alert-tabs .tab').forEach(t => {
    t.classList.remove('active');
    t.setAttribute('aria-selected', 'false');
    t.setAttribute('tabindex', '-1');
  });
  tab.classList.add('active');
  tab.setAttribute('aria-selected', 'true');
  tab.setAttribute('tabindex', '0');
  const panel = document.querySelector('[role="tabpanel"]');
  document.querySelectorAll('[role="tabpanel"]').forEach(p => p.setAttribute('aria-hidden', 'true'));
  panel?.setAttribute('aria-hidden', 'false');
  const type = tab.dataset.type || '';
  panel.id = `tab-panel-${type || 'all'}`;
  panel.setAttribute('aria-labelledby', tab.id);
  const select = document.getElementById('filter-type');
  if (select) select.value = type;
  const url = new URL(window.location);
  if (type) url.searchParams.set('type', type);
  else url.searchParams.delete('type');
  history.pushState({}, '', url);
  localStorage.setItem('admin-alert-tab', type);
  lastTimestamp = null;
  loadAlerts();
  subscribeToRealtime();
}

function initThemeToggle() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const saved = localStorage.getItem('theme') || document.documentElement.getAttribute('data-theme');
  document.documentElement.setAttribute('data-theme', saved);
  btn.textContent = saved === 'dark' ? 'Light Mode' : 'Dark Mode';
  btn.title = saved === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
  btn.addEventListener('click', () => {
    document.documentElement.classList.add('theme-transition');
    setTimeout(() => {
      document.documentElement.classList.remove('theme-transition');
    }, 300);
    const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'parchment' : 'dark';
    document.documentElement.setAttribute('data-theme', current);
    localStorage.setItem('theme', current);
    btn.textContent = current === 'dark' ? 'Light Mode' : 'Dark Mode';
    btn.title = current === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
  });
}
