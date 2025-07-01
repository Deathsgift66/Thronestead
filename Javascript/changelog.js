// Project Name: Thronestead©
// File Name: changelog.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

// JavaScript for changelog.html — fetches and renders changelog updates

document.addEventListener('DOMContentLoaded', () => {
  loadChangelog();

  // Bind refresh button
  document.getElementById('refresh-log')?.addEventListener('click', () => {
    loadChangelog(true);
  });
});

// Fetch changelog from backend and inject into HTML
async function loadChangelog(forceRefresh = false) {
  const container = document.getElementById('changelog-entries');
  container.innerHTML = '<p>Loading updates...</p>';

  try {
    const res = await fetch(`/api/system/changelog${forceRefresh ? '?refresh=true' : ''}`);
    if (!res.ok) throw new Error('Failed to load changelog.');

    const entries = await res.json();
    container.innerHTML = '';

    if (entries.length === 0) {
      container.innerHTML = '<p>No changelog entries available.</p>';
      return;
    }

    entries.forEach(entry => {
      const section = document.createElement('section');
      section.classList.add('changelog-entry');

      const date = new Date(entry.date).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      });

      section.innerHTML = `
        <h3>${entry.title} <span class="version-tag">v${entry.version}</span></h3>
        <p class="entry-date">${date}</p>
        <ul>
          ${entry.changes.map(change => `<li>🔧 ${change}</li>`).join('')}
        </ul>
      `;

      container.appendChild(section);
    });

  } catch (err) {
    console.error('Error fetching changelog:', err);
    container.innerHTML = `<p class="error-msg">Unable to load changelog at this time. Please try again later.</p>`;
  }
}
