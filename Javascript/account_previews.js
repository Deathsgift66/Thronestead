// Project Name: Thronestead©
// File Name: account_previews.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66

function setupPreview(inputId, previewId, fallback = '') {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);

  if (!input || !preview) return;

  input.addEventListener('input', e => {
    const url = e.target.value.trim();
    preview.src = isValidURL(url) ? url : fallback;
  });
}

function isValidURL(str) {
  try {
    new URL(str);
    return true;
  } catch {
    return false;
  }
}

setupPreview('avatar_url', 'avatar-preview', '/images/default-avatar.png');
setupPreview('profile_banner', 'banner-preview', '/images/default-banner.jpg');
