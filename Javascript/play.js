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
    .maybeSingle();

  if (error && profile !== null) {
    console.error('❌ Error loading profile:', error);
    showToast('Failed to load profile.');
    return;
  }

  if (profile && profile.setup_complete) {
    window.location.href = 'overview.html';
    return;
  }

  if (profile) {
    kingdomId = profile.kingdom_id;
    document.getElementById('greeting').textContent = `Welcome, ${escapeHTML(profile.display_name)}!`;
  } else {
    document.getElementById('greeting').textContent = `Welcome, ${escapeHTML(currentUser.user_metadata.display_name)}!`;
  }

  bindEvents(profile);
});

function bindEvents(profileExists) {
  const createBtn = document.getElementById('create-kingdom-btn');

  createBtn.addEventListener('click', async () => {
    const kNameEl = document.getElementById('kingdom-name-input');
    const regionEl = document.getElementById('region-select');
    const villageEl = document.getElementById('village-name-input');

    const kingdomName = kNameEl.value.trim();
    const region = regionEl.value;
    const villageName = villageEl.value.trim();

    if (kingdomName.length < 3) {
      showToast('Kingdom name must be at least 3 characters.');
      return;
    }
    if (!region) {
      showToast('Please select a region.');
      return;
    }
    if (villageName.length < 3) {
      showToast('Village name must be at least 3 characters.');
      return;
    }

    createBtn.disabled = true;

    try {
      if (!profileExists) {
        const { error: userErr } = await supabase.from('users').insert({
          user_id: currentUser.id,
          username: currentUser.user_metadata.username,
          display_name: currentUser.user_metadata.display_name,
          email: currentUser.email
        });
        if (userErr && userErr.code !== '23505') throw userErr;
      }

      const { data: kingdomData, error: kErr } = await supabase
        .from('kingdoms')
        .insert({ user_id: currentUser.id, kingdom_name: kingdomName, region })
        .select('kingdom_id')
        .single();
      if (kErr) throw kErr;

      kingdomId = kingdomData.kingdom_id;

      const { error: villageErr } = await supabase
        .from('villages')
        .insert({ kingdom_id: kingdomId, village_name: villageName });
      if (villageErr) throw villageErr;

      await supabase.from('kingdom_resources').insert({ kingdom_id: kingdomId });

      await supabase
        .from('users')
        .update({ setup_complete: true, kingdom_id: kingdomId })
        .eq('user_id', currentUser.id);

      showToast('Kingdom created!');
      setTimeout(() => {
        window.location.href = 'overview.html';
      }, 1500);
    } catch (err) {
      console.error('❌ Error creating kingdom:', err);
      showToast('Failed to create kingdom.');
      createBtn.disabled = false;
    }
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
