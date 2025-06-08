/*
Project Name: Kingmakers Rise Frontend
File Name: account_settings.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';


document.addEventListener('DOMContentLoaded', async () => {
  try {
    // Fetch User
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) throw new Error('Unauthorized');

    // Fetch User Profile
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('user_id', user.id)
      .single();

    if (error) throw new Error('Failed to load account data: ' + error.message);


    // Prefill Form
    document.getElementById('display_name').value = data.display_name || '';
    document.getElementById('kingdom_name').value = data.kingdom_name || '';
    document.getElementById('profile_bio').value = data.profile_bio || '';
    document.getElementById('email').value = user.email;
    document.getElementById('kingdom_banner').value = data.kingdom_banner || '';
    document.getElementById('avatar_icon').value = data.avatar_icon || '';
    document.getElementById('nameplate_color').value = data.nameplate_color || '#bfa24b';

    document.getElementById('notifications_opt_in').checked = !!data.notifications_opt_in;
    document.getElementById('bg_toggle').checked = !!data.use_play_background;

    // VIP Status via API
    const vipRes = await fetch('/api/kingdom/vip_status', {
      headers: { 'X-User-ID': user.id }
    });
    const vipData = await vipRes.json();
    const vipElement = document.getElementById('vip-status');
    const level = vipData.vip_level || 0;
    vipElement.innerText = level > 0 ? `VIP ${level}` : 'Not a VIP';
    vipElement.title = 'Your current VIP status in Kingmaker\'s Rise';

  } catch (err) {
    console.error('❌ Error loading account:', err);
    alert('❌ Failed to load account settings. Please try again later.');
    window.location.href = 'index.html';
  }
});

// Save Changes
document.getElementById('account-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  // Disable button and show loading state
  const submitBtn = e.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.innerText = 'Saving...';

  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('Unauthorized');

    const updates = {
      display_name: document.getElementById('display_name').value,
      kingdom_name: document.getElementById('kingdom_name').value,
      profile_bio: document.getElementById('profile_bio').value,
      kingdom_banner: document.getElementById('kingdom_banner').value,
      avatar_icon: document.getElementById('avatar_icon').value,
      nameplate_color: document.getElementById('nameplate_color').value,
      notifications_opt_in: document.getElementById('notifications_opt_in').checked,
      use_play_background: document.getElementById('bg_toggle').checked
    };


    const { error: updateError } = await supabase
      .from('users')
      .update(updates)
      .eq('user_id', user.id);

    if (updateError) throw new Error('Failed to save changes: ' + updateError.message);


    // Update Password if entered
    const newPassword = document.getElementById('new_password').value;
    if (newPassword) {
      if (!validatePasswordComplexity(newPassword)) {
        throw new Error(
          "Password should contain at least one character of each: abcdefghijklmnopqrstuvwxyz, ABCDEFGHIJKLMNOPQRSTUVWXYZ, 0123456789, !@#$%^&*()_+-=[]{};':\"|<>?,./`~."
        );
      }
      const { error: pwError } = await supabase.auth.updateUser({ password: newPassword });
      if (pwError) throw new Error('Failed to update password: ' + pwError.message);
    }

    // Final confirmation
    alert('✅ Changes saved successfully!');
    document.getElementById('new_password').value = ''; // Clear password field
    try {
      await fetch('/api/audit-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          action: 'update_profile',
          details: 'Updated account settings'
        })
      });
    } catch (err) {
      console.error('Audit log failed:', err);
    }
  } catch (err) {
    console.error('❌ Error during save:', err);
    alert(err.message);
  } finally {
    // Re-enable button
    submitBtn.disabled = false;
    submitBtn.innerText = 'Save Changes';
  }
});

// Logout Support (safe check for missing button)
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
  logoutBtn.addEventListener('click', async () => {
    try {
      await supabase.auth.signOut();
      window.location.href = 'index.html';
    } catch (err) {
      console.error('❌ Logout failed:', err);
      alert('❌ Failed to logout. Please try again.');
    }
  });
} else {
  console.warn('⚠️ Logout button not found in DOM');
}

// ✅ Helper: Password Complexity
function validatePasswordComplexity(password) {
  const lower = /[a-z]/;
  const upper = /[A-Z]/;
  const digit = /[0-9]/;
  const special = /[!@#$%^&*()_+\-=[\]{};':"\\|<>?,./`~]/;
  return (
    lower.test(password) &&
    upper.test(password) &&
    digit.test(password) &&
    special.test(password)
  );
}
