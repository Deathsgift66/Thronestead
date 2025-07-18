// Project Name: Thronestead©
// File Name: account_previews.js
// Version: 7/18/2025
// Developer: Deathsgift66

/**
 * Dynamically updates a preview image based on an input URL field.
 * @param {string} inputId - The ID of the input element
 * @param {string} previewId - The ID of the preview element (e.g. <img>)
 * @param {string} fallback - Default fallback image URL
 */
function setupPreview(inputId, previewId, fallback = '') {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);

  if (!input || !preview) {
    console.warn(`[account_previews] Missing input or preview for ${inputId}`);
    return;
  }

  const updatePreview = () => {
    const raw = input.value?.trim() || '';
    preview.src = isValidURL(raw) ? raw : fallback;
  };

  input.addEventListener('input', updatePreview);
  input.addEventListener('paste', () => {
    // Paste delay for value to be available
    setTimeout(updatePreview, 0);
  });

  // Initialize preview on page load
  updatePreview();
}

/**
 * Checks whether a string is a valid URL (https/http only)
 * @param {string} str
 * @returns {boolean}
 */
function isValidURL(str) {
  try {
    const url = new URL(str);
    return ['http:', 'https:'].includes(url.protocol);
  } catch {
    return false;
  }
}

// Avatar and banner previews
setupPreview('avatar_url', 'avatar-preview', '/images/default-avatar.png');
setupPreview('profile_banner', 'banner-preview', '/images/default-banner.jpg');
