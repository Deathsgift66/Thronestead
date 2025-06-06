/*
Project Name: Kingmakers Rise Frontend
File Name: forgot_password.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const forgotForm = document.getElementById('forgot-form');
const emailInput = document.getElementById('forgot-email');
const messageContainer = document.getElementById('message');

forgotForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const email = emailInput.value.trim();

  if (!email) {
    messageContainer.textContent = 'Please enter a valid email.';
    return;
  }

  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: 'https://www.kingmakersrise.com/update-password'
    });

    if (error) {
      messageContainer.textContent = 'Error: ' + error.message;
    } else {
      messageContainer.textContent = 'Reset link sent! Check your email.';
    }
  } catch (err) {
    messageContainer.textContent = `Unexpected error: ${err.message}`;
  }
});
