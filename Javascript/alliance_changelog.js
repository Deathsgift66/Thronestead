// Project Name: Thronestead©
// File Name: alliance_changelog.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

import { supabase } from '/Javascript/supabaseClient.js';
import { escapeHTML, formatDate, debounce, showToast, toggleLoading } from '/Javascript/utils.js';
import { authFetchJson } from '/Javascript/fetchJson.js';

let changelogData = [];
let fetchTimer;
let backoff = 30000;
const MAX_BACKOFF = 120000;
let isFetching = false;

const iconMap = {
  war: '🛡',
  treaty: '📜',
  project: '🛠',
  quest: '🗺',
  member: '👤',
  admin: '⚙'
};

function getIcon(type) {
  return iconMap[type] || '📝';
}

function loadFilters() {
  ['start', 'end', 'type'].forEach(key => {
    const val = sessionStorage.getItem('clog-' + key);
    const el = document.getElementById(`filter-${key}`);
    if (el && val) el.value = val;
  });
}

function saveFilters() {
  ['start', 'end', 'type'].forEach(key => {
    const el = document.getElementById(`filter-${key}`);
    if (el && el.value) sessionStorage.setItem('clog-' + key, el.value);
    else sessionStorage.removeItem('clog-' + key);
  });
}

async function fetchChangelog(manual = false) {
  if (isFetching) return;
  isFetching = true;
  toggleLoading(true);
  setButtonsDisabled(true);
  try {
    const { data: { session } = {} } = await supabase.auth.getSession();
    if (!session) {
      const list = document.getElementById('changelog-list');
      if (list) list.innerHTML = '<li class="error-state">Not logged in. Redirecting...</li>';
      return setTimeout(() => { window.location.href = 'login.html'; }, 100);
    }

    const filters = ['start', 'end', 'type'].reduce((params, key) => {
      const val = document.getElementById(`filter-${key}`)?.value;
      if (val && /^\d{4}-\d{2}-\d{2}$/.test(val)) {
        let v = val;
        if (key === 'start') v += 'T00:00:00Z';
        if (key === 'end') v += 'T23:59:59Z';
        params.set(key, v);
      } else if (val) {
        params.set(key, val);
      }
      return params;
    }, new URLSearchParams());

    filters.set('ts', Date.now());
    const data = await authFetchJson(`/api/alliance/changelog?${filters}`);
    changelogData = Array.isArray(data.logs) ? data.logs : [];
    saveFilters();

    updateLastUpdated(data.last_updated);
    renderChangelog(changelogData);
    backoff = 30000;
  } catch (err) {
    console.error('❌ Error fetching changelog:', err);
    const list = document.getElementById('changelog-list');
    if (list) list.innerHTML = '<li class="error-state">Failed to load changelog.</li>';
    updateSummary([]);
    backoff = Math.min(backoff * 2, MAX_BACKOFF);
  } finally {
    isFetching = false;
    toggleLoading(false);
    setButtonsDisabled(false);
    if (manual) backoff = 30000;
    scheduleNextFetch();
  }
}

function scheduleNextFetch() {
  clearTimeout(fetchTimer);
  fetchTimer = setTimeout(fetchChangelog, backoff);
}

function applyFilters() {
  saveFilters();
  fetchChangelog(true);
}

function clearFilters() {
  ['start', 'end', 'type'].forEach(key => {
    const el = document.getElementById(`filter-${key}`);
    if (el) el.value = '';
    sessionStorage.removeItem('clog-' + key);
  });
  fetchChangelog(true);
}

function formatCsvDate(ts) {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return '';
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function updateLastUpdated(timestamp) {
  const el = document.getElementById('last-updated');
  if (el && timestamp) el.textContent = new Date(timestamp).toLocaleString('en-US', { timeZoneName: 'short' });
}

function updateSummary(logs) {
  const start = document.getElementById('filter-start')?.value;
  const end = document.getElementById('filter-end')?.value;
  const type = document.getElementById('filter-type')?.value;
  const parts = [];
  if (type) parts.push(type.charAt(0).toUpperCase() + type.slice(1) + 's');
  if (start) parts.push('from ' + new Date(start).toLocaleDateString());
  if (end) parts.push('to ' + new Date(end).toLocaleDateString());
  const desc = parts.length ? parts.join(' ') : 'all entries';
  const count = logs.length;
  const text = `Showing ${count} ${count === 1 ? 'result' : 'results'} — ${desc}`;
  const el = document.getElementById('results-summary');
  if (el) el.textContent = text;
}

function renderChangelog(logs) {
  const container = document.getElementById('changelog-list');
  if (!container) return;

  if (!logs.length) {
    container.innerHTML = '<li class="empty-state">No historical records match your filters. Adjust the date range or event type and try again.</li>';
    updateSummary(logs);
    return;
  }

  container.innerHTML = logs
    .map((log, idx) => {
      const validTime = log.timestamp && !isNaN(new Date(log.timestamp));
      const timeId = `time-${idx}`;
      const descId = `desc-${idx}`;
      const timeHtml = validTime
        ? `<time id="${timeId}" datetime="${log.timestamp}" aria-label="${new Date(log.timestamp).toLocaleString()}">${formatDate(log.timestamp)}</time>`
        : '<span class="no-time" aria-label="No timestamp">—</span>';
      return `
      <li class="timeline-entry ${escapeHTML(log.event_type)}" role="article" aria-expanded="true" aria-labelledby="${descId} ${timeId}">
        <div class="timeline-bullet"></div>
        <div class="timeline-content">
          <span class="log-icon" role="img" aria-label="${escapeHTML(log.event_type)} event">${getIcon(log.event_type)}</span>
          <span class="log-type ${escapeHTML(log.event_type)}">${escapeHTML(log.event_type.toUpperCase())}</span>
          <p class="log-text" id="${descId}">${escapeHTML(log.description)}</p>
          ${timeHtml}
        </div>
      </li>`;
    })
    .join('');

  container.querySelectorAll('.timeline-entry').forEach(entry => {
    entry.addEventListener('click', () => {
      entry.classList.toggle('collapsed');
      entry.setAttribute('aria-expanded', entry.classList.contains('collapsed') ? 'false' : 'true');
    });
  });

  updateSummary(logs);
}

function exportCSV() {
  if (!changelogData.length) return;
  const header = 'Timestamp,Type,Description\n';
  const csv = changelogData
    .map(l => [formatCsvDate(l.timestamp), l.event_type, l.description].map(v => `"${String(v).replace(/"/g, '""')}"`).join(','))
    .join('\n');
  const blob = new Blob(["\uFEFF" + header + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `alliance_changelog_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('CSV exported', 'success');
}

function bindEvent(id, handler) {
  document.getElementById(id)?.addEventListener('click', handler);
}

function setButtonsDisabled(disabled) {
  ['apply-filters-btn', 'clear-filters-btn', 'refresh-btn', 'export-csv-btn'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = disabled;
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadFilters();
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => fetchChangelog());
  } else {
    setTimeout(fetchChangelog);
  }
  const debouncedApply = debounce(applyFilters, 400);
  bindEvent('apply-filters-btn', debouncedApply);
  const debouncedRefresh = debounce(() => fetchChangelog(true), 100);
  bindEvent('refresh-btn', debouncedRefresh);
  bindEvent('clear-filters-btn', clearFilters);
  bindEvent('export-csv-btn', exportCSV);
  window.addEventListener('beforeunload', () => clearTimeout(fetchTimer));
});

export { applyFilters, fetchChangelog };

