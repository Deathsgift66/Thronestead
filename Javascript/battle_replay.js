/*
Project Name: Kingmakers Rise Frontend
File Name: battle_replay.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Full polished Battle Replay system

import { supabase } from './supabaseClient.js';

let currentStep = 0;
let replayInterval = null;
let timelineSteps = [];

// ✅ DOMContentLoaded
document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "index.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load
  await loadBattleReplay();

  // ✅ Bind Play button
  document.getElementById("play-replay").addEventListener("click", () => {
    if (replayInterval) return; // already playing
    replayInterval = setInterval(playNextStep, 1000);
  });

  // ✅ Bind Pause button
  document.getElementById("pause-replay").addEventListener("click", () => {
    clearInterval(replayInterval);
    replayInterval = null;
  });

  // ✅ Bind Reset button
  document.getElementById("reset-replay").addEventListener("click", resetReplay);
});

// ✅ Load Battle Replay
async function loadBattleReplay() {
  const timelineList = document.getElementById("timeline-list");
  const statusText = document.getElementById("battle-status");
  const winnerText = document.getElementById("winner-name");
  const rewardsSection = document.getElementById("rewards-section");

  timelineList.innerHTML = "<li>Loading battle timeline...</li>";
  statusText.textContent = "";
  winnerText.textContent = "";
  rewardsSection.innerHTML = "<p>Loading rewards...</p>";

  try {
    const res = await fetch("/api/battle-replay");
    const data = await res.json();

    // Populate timeline
    timelineSteps = data.timeline || [];
    timelineList.innerHTML = "";

    if (timelineSteps.length === 0) {
      timelineList.innerHTML = "<li>No battle events found.</li>";
    } else {
      timelineSteps.forEach((event, index) => {
        const li = document.createElement("li");
        li.textContent = `Turn ${index + 1}: ${event}`;
        li.dataset.step = index;
        timelineList.appendChild(li);
      });
    }

    // Populate status and winner
    statusText.textContent = data.outcome?.status || "Unknown";
    winnerText.textContent = data.outcome?.winner || "Unknown";

    // Populate rewards
    rewardsSection.innerHTML = "";
    if (data.rewards && data.rewards.length > 0) {
      const rewardsList = document.createElement("ul");
      data.rewards.forEach(reward => {
        const li = document.createElement("li");
        li.textContent = reward;
        rewardsList.appendChild(li);
      });
      rewardsSection.appendChild(rewardsList);
    } else {
      rewardsSection.innerHTML = "<p>No rewards from this battle.</p>";
    }

    // Reset replay state
    resetReplay();

  } catch (err) {
    console.error("❌ Error loading battle replay:", err);
    timelineList.innerHTML = "<li>Failed to load battle timeline.</li>";
    rewardsSection.innerHTML = "<p>Failed to load rewards.</p>";
  }
}

// ✅ Play next step
function playNextStep() {
  const timelineList = document.getElementById("timeline-list");
  const steps = Array.from(timelineList.children);

  if (currentStep >= steps.length) {
    clearInterval(replayInterval);
    replayInterval = null;
    alert("🎉 Replay finished!");
    return;
  }

  // Highlight current step
  steps.forEach((item, index) => {
    item.style.backgroundColor = index === currentStep ? "var(--gold)" : "";
  });

  currentStep++;
}

// ✅ Reset replay
function resetReplay() {
  const timelineList = document.getElementById("timeline-list");
  Array.from(timelineList.children).forEach(item => {
    item.style.backgroundColor = "";
  });
  currentStep = 0;
  clearInterval(replayInterval);
  replayInterval = null;
}
