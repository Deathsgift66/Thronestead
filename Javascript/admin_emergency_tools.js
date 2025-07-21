import {
  authJsonFetch,
  escapeHTML,
  showToast,
  openModal,
  closeModal,
  toggleLoading,
  debounce,
  postAction,
  applyFilter,
  getNumberInputValue
} from '/Javascript/utils_admin.js';

let pendingAction = null;
let backupList;
let backupFilter;
let debouncedFilter;

const filterQueues = () => {
  const term = backupFilter?.value.toLowerCase() || '';
  if (backupList) applyFilter(backupList, term);
};

async function loadBackups(btn) {
  const list = document.getElementById('backup-list');
  if (!list) return;
  btn?.setAttribute('disabled', 'disabled');
  list.innerHTML = '<li>Loading...</li>';
  toggleLoading(true);
  try {
    const data = await authJsonFetch('/api/admin/emergency/backups', {
      referrerPolicy: 'strict-origin'
    });
    list.innerHTML = '';
    (data.queues || []).forEach(queue => {
      const li = document.createElement('li');
      li.dataset.queue = queue.toLowerCase();
      li.textContent = escapeHTML(queue);
      li.setAttribute('role', 'listitem');
      list.appendChild(li);
    });
    if (!list.children.length) {
      list.innerHTML = '<li class="placeholder">No backups found</li>';
    }
    const time = document.getElementById('backup-time');
    if (time) time.textContent = `Last loaded: ${new Date().toLocaleString()}`;
    filterQueues();
    if (backupFilter && !debouncedFilter) {
      debouncedFilter = debounce(() => filterQueues(), 300);
      backupFilter.addEventListener('input', () => {
        if (backupFilter.value === '') {
          debouncedFilter.cancel();
          filterQueues();
        } else {
          debouncedFilter();
        }
      });
    }
    showToast('Backups loaded', 'success');
  } catch (err) {
    console.error('Failed to load backups:', err);
    list.innerHTML = '<li>Error loading queues</li>';
    showToast('Failed to load backups', 'error');
  } finally {
    btn?.removeAttribute('disabled');
    toggleLoading(false);
  }
}

async function loadActions(btn) {
  const list = document.getElementById('recent-actions-list');
  if (!list) return;
  btn.dataset.originalText = btn.textContent;
  btn.textContent = 'Loading...';
  btn.disabled = true;
  toggleLoading(true);
  try {
    const data = await authJsonFetch('/api/admin/audit-log?limit=20', {
      referrerPolicy: 'strict-origin'
    });
    list.innerHTML = '';
    const allowed = new Set(['reprocess_tick','recalculate_resources','rollback_quest']);
    (data.logs || []).filter(l => allowed.has(l.action)).forEach(log => {
      const li = document.createElement('li');
      li.textContent = `${escapeHTML(log.action)} - ${new Date(log.created_at).toLocaleString()}`;
      list.appendChild(li);
    });
    if (!list.children.length) {
      list.innerHTML = '<li class="placeholder">No actions found</li>';
    }
    showToast('Actions loaded', 'success');
  } catch (err) {
    console.error('Failed to load actions', err);
    list.innerHTML = '<li class="placeholder">Error loading actions</li>';
    showToast('Failed to load actions', 'error');
  } finally {
    btn.textContent = btn.dataset.originalText;
    btn.disabled = false;
    toggleLoading(false);
  }
}

const actions = {
  'reprocess-tick-btn': {
    endpoint: '/api/admin/emergency/reprocess_tick',
    payload: () => {
      try {
        return { war_id: getNumberInputValue('tick-war-id') };
      } catch {
        return { war_id: null };
      }
    },
    success: 'Tick reprocessed',
    confirm: true,
    confirmTitle: 'Reprocess War Tick?'
  },
  'recalc-res-btn': {
    endpoint: '/api/admin/emergency/recalculate_resources',
    payload: () => {
      try {
        return { kingdom_id: getNumberInputValue('recalc-kingdom-id') };
      } catch {
        return { kingdom_id: null };
      }
    },
    success: 'Resources recalculated',
    confirmTitle: 'Recalculate Resources?'
  },
  'rollback-quest-btn': {
    endpoint: '/api/admin/emergency/rollback_quest',
    payload: () => {
      try {
        return {
          alliance_id: getNumberInputValue('quest-alliance-id'),
          quest_code: document.getElementById('quest-code')?.value.trim()
        };
      } catch {
        return { alliance_id: null, quest_code: null };
      }
    },
    success: 'Quest rolled back',
    confirm: true,
    confirmTitle: 'Rollback Quest?'
  },
  'load-backups-btn': {
    action: loadBackups
  },
  'load-actions-btn': {
    action: loadActions
  }
};

document.addEventListener('DOMContentLoaded', () => {
  backupList = document.getElementById('backup-list');
  backupFilter = document.getElementById('backup-filter');
  Object.entries(actions).forEach(([btnId, config]) => {
    const btn = document.getElementById(btnId);
    if (!btn) return;

    btn.addEventListener('click', async () => {
      const execute = async () => {
        if (typeof config.action === 'function') return config.action(btn);

        const payload = config.payload();
        const section = btn.closest('fieldset');
        section?.classList.add('loading');
        section?.setAttribute('aria-busy', 'true');
        ['tick-war-id','recalc-kingdom-id','quest-alliance-id','quest-code'].forEach(id => {
          const el = document.getElementById(id);
          if (el) el.removeAttribute('aria-invalid');
        });
        if (Object.values(payload).some(v => v === null || v === '')) {
          Object.entries(payload).forEach(([k,v]) => {
            const el = document.getElementById(k.replace(/_/g,'-'));
            if ((v === null || v === '') && el) el.setAttribute('aria-invalid','true');
          });
          section?.classList.remove('loading');
          section?.setAttribute('aria-busy','false');
          return showToast('⚠️ All fields required', 'error');
        }
        if (payload.quest_code && !/^[A-Za-z0-9_\-]{1,20}$/.test(payload.quest_code)) {
          document.getElementById('quest-code')?.setAttribute('aria-invalid','true');
          section?.classList.remove('loading');
          section?.setAttribute('aria-busy','false');
          return showToast('Quest code must be alphanumeric, dashes or underscores. Max 20 characters.', 'error');
        }

        btn.disabled = true;
        btn.dataset.originalText = btn.textContent;
        btn.textContent = 'Processing...';
        toggleLoading(true);
        try {
          await postAction(config.endpoint, payload);
          showToast(`✅ ${config.success}`, 'success');
        } catch (err) {
          console.error(`${config.endpoint} failed:`, err);
          const msg = err && err.message ? err.message : 'Request failed';
          showToast(`❌ ${escapeHTML(msg)}`, 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = btn.dataset.originalText;
          toggleLoading(false);
          section?.classList.remove('loading');
          section?.setAttribute('aria-busy','false');
        }
      };

      if (config.confirm) {
        pendingAction = execute;
        document.getElementById('confirm-title').textContent = config.confirmTitle || 'Confirm Action';
        openModal('confirm-modal');
        document.getElementById('main')?.setAttribute('inert', '');
        document.getElementById('navbar-container')?.setAttribute('inert', '');
      } else {
        execute();
      }
    });
  });

  const confirmYes = document.getElementById('confirm-yes');
  const confirmNo = document.getElementById('confirm-no');
  confirmYes?.addEventListener('click', async () => {
    confirmYes.textContent = 'Confirming...';
    confirmYes.disabled = true;
    await pendingAction?.();
    pendingAction = null;
    confirmYes.disabled = false;
    confirmYes.textContent = 'Yes';
    closeModal('confirm-modal');
    document.getElementById('main')?.removeAttribute('inert');
    document.getElementById('navbar-container')?.removeAttribute('inert');
  });
  confirmNo?.addEventListener('click', () => {
    closeModal('confirm-modal');
    document.getElementById('main')?.removeAttribute('inert');
    document.getElementById('navbar-container')?.removeAttribute('inert');
    pendingAction = null;
  });

  document.addEventListener('keydown', e => {
    const modal = document.getElementById('confirm-modal');
    if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
      closeModal('confirm-modal');
      document.getElementById('main')?.removeAttribute('inert');
      document.getElementById('navbar-container')?.removeAttribute('inert');
      pendingAction = null;
    }
  });
});
