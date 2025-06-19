// Project Name: Thronestead©
// File Name: account_previews.js
// Version 6.17.2025.00.00
// Developer: Codex

document.getElementById('avatar_url')?.addEventListener('input', e => {
  const preview = document.getElementById('avatar-preview');
  if (preview) preview.src = e.target.value;
});

document.getElementById('profile_banner')?.addEventListener('input', e => {
  const preview = document.getElementById('banner-preview');
  if (preview) preview.src = e.target.value;
});
