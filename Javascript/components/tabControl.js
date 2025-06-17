// Project Name: Thronestead©
// File Name: tabControl.js
// Version 6.15.2025.21.00
// Developer: Codex

/**
 * Simple tab controller. Adds click handlers for elements
 * matching `buttonSelector` and toggles `active` class on
 * both the button and the matching section by id.
 *
 * @param {object} options
 * @param {string} [options.buttonSelector='.tab-button'] CSS selector for tab buttons
 * @param {string} [options.sectionSelector='.tab-section'] CSS selector for tab sections
 * @param {Function} [options.onShow] Callback fired after a tab is shown
 */
export function setupTabs({
  buttonSelector = '.tab-button',
  sectionSelector = '.tab-section',
  onShow = null
} = {}) {
  const buttons = Array.from(document.querySelectorAll(buttonSelector));
  const sections = Array.from(document.querySelectorAll(sectionSelector));
  if (!buttons.length) return;

  const show = id => {
    buttons.forEach(b => b.classList.toggle('active', b.dataset.tab === id));
    sections.forEach(s => s.classList.toggle('active', s.id === id));
    if (onShow) onShow(id);
  };

  buttons.forEach(btn => btn.addEventListener('click', () => show(btn.dataset.tab)));

  // Activate first tab if none marked active
  const initial = buttons.find(b => b.classList.contains('active'))?.dataset.tab || buttons[0].dataset.tab;
  show(initial);
  return show;
}
