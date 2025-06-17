// Project Name: Thronestead©
// File Name: sovereign_utils.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
// Sovereign’s Grand Overseer — Shared Utility Module
// Central module to manage village cards, sorting, and ambience audio.

/**
 * @namespace SovereignUtils
 * @description Utility functions for the Sovereign’s Grand Overseer page.
 */
export const SovereignUtils = {

  /**
   * Create a village card DOM element.
   * @param {Object} village - Village data from the backend.
   * @param {number} village.village_id
   * @param {string} village.village_name
   * @param {number} village.population
   * @param {number} village.building_count
   * @param {number} village.troop_count
   * @param {boolean} village.is_empty
   * @returns {HTMLElement} - A formatted card element.
   */
  createVillageCard(village) {
    const card = document.createElement('div');
    card.className = 'village-card';
    card.setAttribute('data-empty', village.is_empty ? 'true' : 'false');
    card.setAttribute('tabindex', '0'); // Accessibility

    card.innerHTML = `
      <h3>${this.escapeHTML(village.village_name)}</h3>
      <p><strong>Population:</strong> ${village.population.toLocaleString()}</p>
      <p><strong>Buildings:</strong> ${village.building_count}</p>
      <p><strong>Military:</strong> ${village.troop_count}</p>
      <button class="action-btn" data-village-id="${village.village_id}" aria-label="Manage ${this.escapeHTML(village.village_name)}">Manage Village</button>
    `;

    // Attach click event to button
    card.querySelector('button').addEventListener('click', () => {
      this.openVillageDetail(village.village_id);
    });

    return card;
  },

  /**
   * Navigate to the village detail page.
   * @param {number} villageId - ID of the village to manage.
   */
  openVillageDetail(villageId) {
    if (villageId && Number.isInteger(villageId)) {
      window.location.href = `village.html?village_id=${villageId}`;
    } else {
      console.warn('Invalid village ID passed to openVillageDetail:', villageId);
    }
  },

  /**
   * Sort village cards in the grid based on a given criteria.
   * @param {string} sortBy - 'name', 'size', or 'resources'.
   */
  sortVillageGrid(sortBy) {
    const grid = document.getElementById('village-grid');
    if (!grid) return;

    const cards = Array.from(grid.querySelectorAll('.village-card'));

    cards.sort((a, b) => {
      const getTextValue = (el, idx) =>
        parseInt(el.querySelector(`p:nth-child(${idx})`)?.textContent.replace(/\D/g, '') || '0', 10);

      switch (sortBy) {
        case 'name':
          return a.querySelector('h3').textContent.localeCompare(b.querySelector('h3').textContent);
        case 'size':
          return getTextValue(b, 2) - getTextValue(a, 2); // population
        case 'resources':
          return getTextValue(b, 3) - getTextValue(a, 3); // buildings
        default:
          return 0;
      }
    });

    cards.forEach(card => grid.appendChild(card)); // Re-render in sorted order
  },

  /**
   * Play ambient tavern-style audio on loop.
   * Adds audio only once.
   */
  playAmbientAudio() {
    let audio = document.getElementById('ambient-audio');
    if (!audio) {
      audio = document.createElement('audio');
      audio.id = 'ambient-audio';
      audio.src = 'Assets/audio/ambient_tavern.mp3'; // Replace with final path
      audio.loop = true;
      audio.volume = 0.4;
      audio.setAttribute('aria-hidden', 'true');
      document.body.appendChild(audio);
    }
    audio.play().catch(err => console.warn('Audio playback failed:', err));
  },

  /**
   * Stop ambient audio if playing.
   */
  stopAmbientAudio() {
    const audio = document.getElementById('ambient-audio');
    if (audio && !audio.paused) {
      audio.pause();
    }
  },

  /**
   * Utility: Sanitize any text for HTML injection.
   * @param {string} str - Unsafe string.
   * @returns {string} - Safe, escaped string.
   */
  escapeHTML(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
};
