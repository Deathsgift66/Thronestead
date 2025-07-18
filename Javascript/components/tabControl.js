// Project: Thronestead©
// File: tabControl.js
// Version: 7/18/2025
// Developer: Deathsgift66

/**
 * Tab controller for UI navigation.
 * Adds accessible tab-switching behavior between buttons and tab sections.
 *
 * @param {Object} options
 * @param {string} [options.buttonSelector='.tab-button'] - CSS selector for tab buttons
 * @param {string} [options.sectionSelector='.tab-section'] - CSS selector for tab content
 * @param {Function} [options.onShow] - Optional callback after tab is shown
 * @returns {Function} showTab - A function to programmatically switch tabs by ID
 */
export function setupTabs({
  buttonSelector = '.tab-button',
  sectionSelector = '.tab-section',
  onShow = null
} = {}) {
  const buttons = Array.from(document.querySelectorAll(buttonSelector));
  const sections = Array.from(document.querySelectorAll(sectionSelector));

  if (buttons.length === 0 || sections.length === 0) {
    console.warn('[TabControl] No tab buttons or sections found.');
    return () => {};
  }

  const tabMap = new Map();
  sections.forEach(sec => tabMap.set(sec.id, sec));

  function showTab(id) {
    if (!tabMap.has(id)) {
      console.warn(`[TabControl] Tab section "${id}" not found.`);
      return;
    }

    buttons.forEach(btn => {
      const isActive = btn.dataset.tab === id;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', String(isActive));
      btn.setAttribute('tabindex', isActive ? '0' : '-1');
    });

    sections.forEach(sec => {
      sec.classList.toggle('active', sec.id === id);
      sec.setAttribute('aria-hidden', sec.id === id ? 'false' : 'true');
    });

    if (typeof onShow === 'function') {
      onShow(id);
    }
  }

  // Bind click events to buttons
  buttons.forEach(btn => {
    const tabId = btn.dataset.tab;
    if (!tabId) return;

    btn.setAttribute('role', 'tab');
    btn.setAttribute('aria-controls', tabId);
    btn.setAttribute('tabindex', '-1');

    btn.addEventListener('click', e => {
      e.preventDefault();
      showTab(tabId);
    });
  });

  // Assign ARIA roles to sections
  sections.forEach(sec => {
    sec.setAttribute('role', 'tabpanel');
    sec.setAttribute('tabindex', '0');
  });

  // Initialize to active or first tab
  const initialBtn = buttons.find(b => b.classList.contains('active')) || buttons[0];
  if (initialBtn) {
    showTab(initialBtn.dataset.tab);
  }

  return showTab;
}
