// Project Name: Thronestead©
// File Name: tabControl.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

/**
 * Tab controller for UI navigation.
 * Automatically toggles 'active' class between tab buttons and content sections.
 *
 * @param {object} options
 * @param {string} [options.buttonSelector='.tab-button'] - Selector for tab buttons
 * @param {string} [options.sectionSelector='.tab-section'] - Selector for tab content sections
 * @param {Function} [options.onShow] - Optional callback fired after a tab is shown
 * @returns {Function} show - A function to manually switch tabs by ID
 */
export function setupTabs({
  buttonSelector = '.tab-button',
  sectionSelector = '.tab-section',
  onShow = null
} = {}) {
  const buttons = Array.from(document.querySelectorAll(buttonSelector));
  const sections = Array.from(document.querySelectorAll(sectionSelector));
  if (buttons.length === 0 || sections.length === 0) return;

  const show = id => {
    if (!id) return;
    buttons.forEach(btn => {
      const isActive = btn.dataset.tab === id;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    sections.forEach(section => {
      const isVisible = section.id === id;
      section.classList.toggle('active', isVisible);
    });

    if (typeof onShow === 'function') {
      onShow(id);
    }
  };

  buttons.forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const tabId = btn.dataset.tab;
      if (tabId) show(tabId);
    });
  });

  // Initial tab: use existing `.active` or default to first button
  const activeBtn = buttons.find(b => b.classList.contains('active'));
  const initialTab = activeBtn?.dataset.tab || buttons[0].dataset.tab;
  show(initialTab);

  return show;
}
