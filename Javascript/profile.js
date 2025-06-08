/*
Project Name: Kingmakers Rise Frontend
File Name: profile.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js already protects this page → no duplicate session check
  // ✅ Initial load
  await loadPlayerProfile();
});

// ✅ Load Player Profile
async function loadPlayerProfile() {
  const avatarImg = document.getElementById("profile-picture");
  const playerNameEl = document.getElementById("player-name");
  const kingdomNameEl = document.getElementById("kingdom-name");
  const mottoEl = document.getElementById("player-motto");
  const vipBadgeEl = document.getElementById("vip-badge");
  const prestigeEl = document.getElementById("prestige-score");
  const titlesListEl = document.getElementById("titles-list");
  const customizationContainer = document.getElementById("profile-customization-content");

  // Placeholders while loading
  playerNameEl.textContent = "Loading...";
  kingdomNameEl.textContent = "Loading...";
  mottoEl.textContent = "Loading...";
  customizationContainer.innerHTML = "<p>Loading customization options...</p>";

  try {
    // ✅ Load user profile
    const { data: { user } } = await supabase.auth.getUser();

    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('user_id', user.id)
      .single();

    if (error) throw error;

    // ✅ Render avatar
    if (data.profile_avatar_url) {
      avatarImg.src = data.profile_avatar_url;
      avatarImg.alt = `${data.username}'s Avatar`;
    } else {
      avatarImg.src = "../Assets/default_avatar.png";
      avatarImg.alt = "Default Avatar";
    }

    // ✅ Render profile info
    playerNameEl.textContent = data.username || "Unnamed Player";
    kingdomNameEl.textContent = data.kingdom_name || "Unnamed Kingdom";
    mottoEl.textContent = data.profile_bio || "No motto set.";

    // ✅ VIP badge via API
    try {
      const vipRes = await fetch('/api/kingdom/vip_status', {
        headers: { 'X-User-ID': user.id }
      });
      const vipData = await vipRes.json();
      const lvl = vipData.vip_level || 0;
      if (lvl > 0) {
        vipBadgeEl.style.display = 'inline-block';
        vipBadgeEl.textContent = `VIP ${lvl}`;
      } else {
        vipBadgeEl.style.display = 'none';
      }
    } catch (e) {
      vipBadgeEl.style.display = 'none';
    }

    // Prestige and titles
    try {
      const [prestigeRes, titlesRes] = await Promise.all([
        fetch('/api/kingdom/prestige', { headers: { 'X-User-ID': user.id } }),
        fetch('/api/kingdom/titles', { headers: { 'X-User-ID': user.id } })
      ]);
      const prestigeData = await prestigeRes.json();
      const titlesData = await titlesRes.json();
      prestigeEl.textContent = `Prestige: ${prestigeData.prestige_score || 0}`;
      titlesListEl.innerHTML = '';
      (titlesData.titles || []).forEach(t => {
        const li = document.createElement('li');
        li.textContent = t;
        titlesListEl.appendChild(li);
      });
    } catch (e) {
      prestigeEl.textContent = 'Prestige: --';
      titlesListEl.innerHTML = '';
    }

    // ✅ Render customization options
    // In future this can load from `profile_customization_catalogue` table
    customizationContainer.innerHTML = `
      <h3>Customize Profile</h3>
      <button class="action-btn">Change Avatar</button>
      <button class="action-btn">Change Banner</button>
      <button class="action-btn">Change Border</button>
      <button class="action-btn">Edit Motto</button>
    `;

    // Example: Bind Edit Motto button
    customizationContainer.querySelectorAll(".action-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        alert('Profile customization will be available in a future update.');
      });
    });

  } catch (err) {
    console.error("❌ Error loading profile:", err);
    playerNameEl.textContent = "Failed to load.";
    kingdomNameEl.textContent = "Failed to load.";
    mottoEl.textContent = "Failed to load.";
    customizationContainer.innerHTML = "<p>Failed to load customization options.</p>";
  }
}
