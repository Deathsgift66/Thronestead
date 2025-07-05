import { supabase } from './supabaseClient.js';

document.getElementById('signup-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const data = {
    email: document.getElementById('email').value.trim(),
    password: document.getElementById('password').value,
    kingdom_name: document.getElementById('kingdom_name').value.trim(),
    region: document.getElementById('region').value.trim(),
    profile_bio: document.getElementById('profile_bio').value.trim()
  };

  const response = await fetch('/api/signup/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });

  const result = await response.json();
  if (response.ok) {
    alert('Signup successful. You may now log in.');
    window.location.href = '/login.html';
  } else {
    alert(result.detail || 'Signup failed. Try again.');
  }
});
