// Project Name: Thronestead©
// File Name: admin_dashboard.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66

import {
  escapeHTML,
  authJsonFetch,
  authFetch,
  showToast,
  debounce,
  updateElementText,
  formatTimestamp
} from '/Javascript/utils.js';
import {
  initCsrf,
  rotateCsrfToken,
  getCsrfToken
} from '/Javascript/security/csrf.js';

const REFRESH_MS = 30000;
let csrfToken = initCsrf();
setInterval(() => {
  csrfToken = rotateCsrfToken();
}, 15 * 60 * 1000);

function setupAutoRefresh() {
  loadDashboardStats();
  loadFlaggedUsers();
  setInterval(async () => {
    if (document.visibilityState !== 'visible') return;
    await loadDashboardStats();
    await loadFlaggedUsers();
  }, REFRESH_MS);
}

let lastStats = {};
let lastStatsTime = 0;
async function loadDashboardStats() {
  try {
    const data = await authJsonFetch(`/api/admin/stats?v=${Date.now()}`);
    if (JSON.stringify(data) === JSON.stringify(lastStats)) return;
    lastStats = data;
    ['total-users', 'total-users-card'].forEach(id =>
      updateElementText(id, data.active_users)
    );
    ['flagged-users', 'sum-flags'].forEach(id =>
      updateElementText(id, data.flagged_users)
    );
    updateElementText('suspicious-activity', data.suspicious_count);
    updateElementText('sum-wars', data.active_wars);
    lastStatsTime = Date.now();
    updateElementText('stats-updated', formatTimestamp(lastStatsTime));
  } catch (e) {
    console.error('⚠️ Dashboard stats error:', e);
  }
}

async function loadPlayerList(page = 1) {
  const q = document.getElementById('search-player')?.value.toLowerCase() || '';
  const status = document.getElementById('status-filter')?.value || '';
  const sort = document.getElementById('sort-order')?.value || 'username-asc';
  const container = document.getElementById('player-list');
  if (!container) return;
  container.textContent = 'Loading...';
  try {
    const url = new URL('/api/admin/search_user', window.location.origin);
    if (q) url.searchParams.set('q', encodeURIComponent(q));
    if (status) url.searchParams.set('status', encodeURIComponent(status));
    url.searchParams.set('page', page);
    let players = await authJsonFetch(url, { referrerPolicy: 'strict-origin-when-cross-origin' });
    if (sort === 'username-desc') {
      players = players.sort((a, b) => b.username.localeCompare(a.username));
    } else {
      players = players.sort((a, b) => a.username.localeCompare(b.username));
    }
    container.innerHTML = '';
    if (!players.length) {
      container.innerHTML = '<p>No players found.</p>';
      return;
    }
    container.appendChild(
      players.reduce((frag, p) => {
        const card = document.createElement('div');
        card.className = 'player-card';
        card.innerHTML = `
          <p><strong>${escapeHTML(p.username)}</strong> (${escapeHTML(p.id)})</p>
          <p>Status: ${escapeHTML(p.status)}</p>
          <div class="player-actions" role="group" aria-label="Moderation Actions">
            ${['flag', 'freeze', 'ban']
              .map(
                action =>
                  `<button class="admin-btn" data-action="${action}" data-id="${escapeHTML(
                    p.id
                  )}">${action.charAt(0).toUpperCase() + action.slice(1)}</button>`
              )
              .join('')}
          </div>`;
        frag.appendChild(card);
        return frag;
      }, document.createDocumentFragment())
    );
  } catch (e) {
    console.error('⚠️ Player list error:', e);
    container.innerHTML = '<p class="error-msg">Failed to fetch players.</p>';
  }
}

async function loadAuditData() {
  const url = new URL('/api/admin/audit/logs', window.location.origin);
  const type = document.getElementById('log-type')?.value.trim();
  const user = document.getElementById('log-user')?.value.trim();
  const startInput = document.getElementById('log-start')?.value;
  const endInput = document.getElementById('log-end')?.value;
  if (type) url.searchParams.set('search', encodeURIComponent(type));
  if (user) url.searchParams.set('user_id', encodeURIComponent(user));
  if (startInput) url.searchParams.set('start_date', new Date(startInput).toISOString());
  if (endInput) url.searchParams.set('end_date', new Date(endInput).toISOString());
  return authJsonFetch(url, { referrerPolicy: 'strict-origin-when-cross-origin' });
}

async function renderAuditLogs() {
  const container = document.getElementById('log-list');
  if (!container) return;
  container.textContent = 'Loading...';
  try {
    const logs = await loadAuditData();
    container.innerHTML = '';
    if (!logs.length) {
      container.innerHTML = '<p>No audit logs found.</p>';
      return;
    }
    container.appendChild(
      logs.reduce((frag, log) => {
        const entry = document.createElement('div');
        entry.className = 'log-card';
        entry.innerHTML = `
          <p><strong>${escapeHTML(log.action)}</strong> — ${escapeHTML(log.details)}</p>
          <p class="log-time">${formatTimestamp(log.created_at)}</p>`;
        frag.appendChild(entry);
        return frag;
      }, document.createDocumentFragment())
    );
  } catch (e) {
    console.error('⚠️ Logs error:', e);
    container.innerHTML = '<p class="error-msg">Failed to fetch audit logs.</p>';
  }
}

let alertSocket;
function connectAlertSocket(retries = 0) {
  const container = document.getElementById('alerts');
  if (!container) return;
  const origin = window.location.origin || location.protocol + '//' + location.host;
  authJsonFetch('/api/admin/alerts/connect', {
    method: 'POST',
    headers: { 'X-CSRF-Token': getCsrfToken() },
    referrerPolicy: 'strict-origin-when-cross-origin'
  })
    .then(connect => {
      const { url: wsPath } = connect;
      alertSocket = new WebSocket(new URL(wsPath, origin).href.replace(/^http/, 'ws'));
      updateElementText('alert-status', '🔄 Connected');
      alertSocket.onmessage = ({ data }) => {
        let alert;
        try {
          alert = JSON.parse(data);
        } catch (err) {
          console.error('Invalid alert payload', err);
          return;
        }
        const el = document.createElement('div');
        el.className = 'alert-item';
        el.innerHTML = `<b>${escapeHTML(alert.type)}</b>: ${escapeHTML(alert.message)} <small>${formatTimestamp(alert.timestamp)}</small>`;
        container.prepend(el);
      };
      alertSocket.onerror = alertSocket.onclose = () => {
        updateElementText('alert-status', '❌ Disconnected');
        const delay = Math.min(30000, 1000 * Math.pow(2, retries));
        console.error('❌ Alert socket error. retry', retries);
        setTimeout(() => connectAlertSocket(retries + 1), delay);
      };
    })
    .catch(err => {
      console.error('Alert connect failed', err);
      updateElementText('alert-status', '❌ Disconnected');
      const delay = Math.min(30000, 1000 * Math.pow(2, retries));
      setTimeout(() => connectAlertSocket(retries + 1), delay);
    });
}

function initAlertSocket() {
  const container = document.getElementById('alerts');
  if (!container) return;
  container.innerHTML = '';
  connectAlertSocket();
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && (!alertSocket || alertSocket.readyState === WebSocket.CLOSED)) {
      connectAlertSocket();
    }
  });
}

function throttleButton(btn, ms = 3000) {
  if (!btn) return;
  btn.disabled = true;
  btn.classList.add('loading-spinner');
  setTimeout(() => {
    btn.disabled = false;
    btn.classList.remove('loading-spinner');
  }, ms);
}

async function handleAdminAction(endpoint, payload, msg, btn) {
  try {
    if (btn) throttleButton(btn);
    await postAdminAction(endpoint, payload);
    showToast(msg, 'success');
    if (btn) {
      btn.classList.add('flash-success');
      setTimeout(() => btn.classList.remove('flash-success'), 600);
    }
  } catch (err) {
    console.error('❌ Action failed:', err);
    showToast(`Action failed: ${err.message}`, 'error');
  }
}

async function postAdminAction(endpoint, payload) {
  const res = await authFetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': getCsrfToken(),
      ReferrerPolicy: 'strict-origin-when-cross-origin'
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
}

const actions = {
  'toggle-flag-btn': async btn => {
    const key = document.getElementById('flag-key').value.trim();
    const value = document.getElementById('flag-value').value === 'true';
    if (!key) return showToast('Enter a flag key', 'error');
    await handleAdminAction('/api/admin/flags/toggle', { flag_key: key, value }, 'Flag updated', btn);
  },
  'update-kingdom-btn': async btn => {
    const id = Number(document.getElementById('kingdom-id').value.trim());
    const field = document.getElementById('kingdom-field').value.trim();
    const value = document.getElementById('kingdom-value').value.trim();
    if (!id || !field) return showToast('Missing field/kingdom', 'error');
    await handleAdminAction(
      '/api/admin/kingdom/update_field',
      { kingdom_id: id, field, value },
      'Kingdom updated',
      btn
    );
  },
  'force-end-war-btn': async btn => {
    const id = Number(document.getElementById('war-id').value.trim());
    if (!id) return showToast('Enter war ID', 'error');
    await handleAdminAction('/api/admin/war/force_end', { war_id: id }, 'War ended', btn);
  },
  'rollback-tick-btn': async btn => {
    const id = Number(document.getElementById('war-id').value.trim());
    if (!id) return showToast('Enter war ID', 'error');
    await handleAdminAction('/api/admin/war/rollback_tick', { war_id: id }, 'Tick rolled back', btn);
  },
  'create-event': async btn => {
    const dlg = document.getElementById('create-event-dialog');
    dlg.showModal();
    dlg.querySelector('input').focus();
    dlg.querySelector('.confirm').onclick = async () => {
      dlg.close();
      const name = dlg.querySelector('input').value.trim();
      if (!name) return showToast('Event name required', 'error');
      await handleAdminAction('/api/admin/events/create', { name }, 'Event created', btn);
    };
    dlg.querySelector('.cancel').onclick = () => dlg.close();
  },
  'publish-news-btn': async btn => {
    const payload = ['title', 'summary', 'content'].reduce((acc, id) => {
      acc[id] = document.getElementById(`news-${id}`).value.trim();
      return acc;
    }, {});
    if (!payload.title || !payload.summary || !payload.content) return showToast('Fill all news fields', 'error');
    await handleAdminAction('/api/admin/news/post', payload, 'News published', btn);
    ['title', 'summary', 'content'].forEach(id => (document.getElementById(`news-${id}`).value = ''));
  }
};

export function init() {
  loadDashboardStats();
  loadPlayerList();
  initAlertSocket();
  loadFlaggedUsers();
  loadFlags();
  setupAutoRefresh();

  const debouncedLoad = debounce(() => loadPlayerList(1), 400);
  document.getElementById('search-btn')?.addEventListener('click', debouncedLoad);
  document.getElementById('search-player')?.addEventListener('keypress', e => {
    if (e.key === 'Enter') debouncedLoad();
  });
  document.getElementById('status-filter')?.addEventListener('change', debouncedLoad);
  document.getElementById('load-logs-btn')?.addEventListener('click', renderAuditLogs);
  document.getElementById('export-csv')?.addEventListener('click', () => loadAuditData('csv'));
  Object.entries(actions).forEach(([id, fn]) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', () => fn(el));
  });
}

document.addEventListener('DOMContentLoaded', init);

window.onerror = (msg, src, line, col, err) => {
  console.error('Window error', msg, err);
};
window.onunhandledrejection = e => {
  console.error('Promise rejection', e.reason);
};
