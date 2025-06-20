import { supabase } from './supabaseClient.js';
import { showToast } from './utils.js';

document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(window.location.hash.substring(1));
  const accessToken = params.get('access_token');

  if (!accessToken) {
    showToast('Missing reset token');
    return;
  }

  const { error } = await supabase.auth.getUser(accessToken);
  if (error) {
    showToast('Invalid or expired link');
    return;
  }

  const form = document.getElementById('reset-form');
  form.style.display = 'block';

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const pw = document.getElementById('new-password').value;
    const { error } = await supabase.auth.updateUser(
      { password: pw },
      { accessToken }
    );
    if (error) {
      showToast('Reset failed');
      return;
    }
    showToast('Password reset. Redirecting...');
    setTimeout(() => (window.location.href = '/login.html'), 1500);
  });
});
