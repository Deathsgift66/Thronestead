// sovereign_utils.js — FINAL AAA/SSS VERSION — 6.2.25
// Sovereign’s Grand Overseer — Shared Utility Module

/**
 * @namespace SovereignUtils
 * @description Utility functions for the Sovereign’s Grand Overseer page.
 */
const SovereignUtils = {

  /**
   * Create a Village Card element.
   * @param {Object} village - The village object from Supabase.
   * @returns {HTMLElement} The DOM element for the village card.
   */
  createVillageCard(village) {
    const card = document.createElement('div');
    card.classList.add('village-card');
    card.setAttribute('data-empty', village.is_empty ? "true" : "false");

    card.innerHTML = `
      <h3>${village.village_name}</h3>
      <p>Population: ${village.population.toLocaleString()}</p>
      <p>Buildings: ${village.building_count}</p>
      <p>Military: ${village.troop_count}</p>
      <button class="action-btn" onclick="SovereignUtils.openVillageDetail(${village.village_id})">Manage Village</button>
    `;

    return card;
  },

  /**
   * Open Village Detail page.
   * @param {number} villageId - The village ID.
   */
  openVillageDetail(villageId) {
    window.location.href = `village.html?village_id=${villageId}`;
  },

  /**
   * Sort the village grid by the selected criterion.
   * @param {string} sortBy - The sort type: name, size, resources.
   */
  sortVillageGrid(sortBy) {
    const grid = document.getElementById('village-grid');
    const cards = Array.from(grid.querySelectorAll('.village-card'));

    cards.sort((a, b) => {
      if (sortBy === "name") {
        return a.querySelector('h3').textContent.localeCompare(b.querySelector('h3').textContent);
      } else if (sortBy === "size") {
        const popA = parseInt(a.querySelector('p:nth-child(2)').textContent.replace(/[^0-9]/g, ''));
        const popB = parseInt(b.querySelector('p:nth-child(2)').textContent.replace(/[^0-9]/g, ''));
        return popB - popA;
      } else if (sortBy === "resources") {
        // Fallback → use building count as proxy
        const bldA = parseInt(a.querySelector('p:nth-child(3)').textContent.replace(/[^0-9]/g, ''));
        const bldB = parseInt(b.querySelector('p:nth-child(3)').textContent.replace(/[^0-9]/g, ''));
        return bldB - bldA;
      }
      return 0;
    });

    // Re-append sorted cards
    cards.forEach(card => grid.appendChild(card));
  },

  /**
   * Play ambient audio.
   */
  playAmbientAudio() {
    let audio = document.getElementById('ambient-audio');
    if (!audio) {
      audio = document.createElement('audio');
      audio.id = 'ambient-audio';
      audio.src = 'Assets/audio/ambient_tavern.mp3'; // Example path — replace with your file
      audio.loop = true;
      audio.volume = 0.5;
      document.body.appendChild(audio);
    }
    audio.play();
  },

  /**
   * Stop ambient audio.
   */
  stopAmbientAudio() {
    const audio = document.getElementById('ambient-audio');
    if (audio) {
      audio.pause();
    }
  }
};
