import { supabase } from '../supabaseClient.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('forgot-form');
  const emailInput = document.getElementById('forgot-email');
  const message = document.getElementById('forgot-message');
  const button = form.querySelector('button');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const email = emailInput.value.trim();
    if (!email) {
      message.textContent = 'Please enter a valid email.';
      return;
    }
    button.disabled = true;
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: 'https://www.thronestead.com/update-password.html'
      });
      message.textContent = error ? `Error: ${error.message}` : 'Reset link sent! Check your email.';
    } catch (err) {
      message.textContent = `Unexpected error: ${err.message}`;
    } finally {
      button.disabled = false;
    }
  });
});
