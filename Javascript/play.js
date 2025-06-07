/*
Project Name: Kingmakers Rise Frontend
File Name: play.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

let currentUser = null;
let kingdomId = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  currentUser = session.user;

  const { data: profile, error } = await supabase
    .from('users')
    .select('setup_complete, kingdom_id, display_name')
    .eq('user_id', currentUser.id)
    .single();

  if (error) {
    console.error('❌ Error loading profile:', error);
    showToast('Failed to load profile.');
    return;
  }

  kingdomId = profile.kingdom_id;

  if (profile.setup_complete) {
    window.location.href = 'overview.html';
    return;
  }

  document.getElementById('greeting').textContent = `Welcome, ${escapeHTML(profile.display_name)}!`;
  bindEvents();
});

function bindEvents() {
  const createBtn = document.getElementById('create-village-btn');
  const continueBtn = document.getElementById('continue-btn');

  createBtn.addEventListener('click', async () => {
    const nameInput = document.getElementById('village-name-input');
    const villageName = nameInput.value.trim();

    if (villageName.length < 3) {
      showToast('Village name must be at least 3 characters.');
      return;
    }

    createBtn.disabled = true;

    const { error } = await supabase
      .from('villages')
      .insert({ kingdom_id: kingdomId, village_name: villageName });

    if (error) {
      console.error('❌ Error creating village:', error);
      showToast('Failed to create village.');
      createBtn.disabled = false;
      return;
    }

    showToast('Village created!');
    document.getElementById('village-step').style.display = 'none';
    document.getElementById('quest-step').style.display = 'block';
    continueBtn.disabled = false;
  });

  continueBtn.addEventListener('click', async () => {
    continueBtn.disabled = true;

    const { error } = await supabase
      .from('users')
      .update({ setup_complete: true })
      .eq('user_id', currentUser.id);

    if (error) {
      console.error('❌ Error updating profile:', error);
      showToast('Failed to complete setup.');
      continueBtn.disabled = false;
      return;
    }

    window.location.href = 'overview.html';
  });
}

function showToast(msg) {
  let toastEl = document.getElementById('toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.id = 'toast';
    toastEl.className = 'toast-notification';
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  setTimeout(() => toastEl.classList.remove('show'), 3000);
}

function escapeHTML(str) {
  return str?.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
