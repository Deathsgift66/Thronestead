/*
Project Name: Kingmakers Rise Frontend
File Name: tutorial.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Tutorial Page Controller — Scroll Animation Only

import { supabase } from './supabaseClient.js';

let currentUser = null;
let tutorialChannel;

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }
  currentUser = session.user;

  await loadSteps();
  setupRealtime();
  initScrollAnimations();
  setupProgressBar();
});

// ✅ Initialize Scroll Animations
function initScrollAnimations() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      } else {
        entry.target.classList.remove('visible');
      }
    });
  }, {
    threshold: 0.1
  });

  document.querySelectorAll('.tutorial-step').forEach(step => {
    observer.observe(step);
  });
}

async function loadSteps() {
  const container = document.getElementById('steps');
  container.innerHTML = '<p>Loading...</p>';
  try {
    const res = await fetch('/api/tutorial/steps', {
      headers: { 'X-User-Id': currentUser.id }
    });
    const data = await res.json();
    renderSteps(data.steps || []);
  } catch (err) {
    console.error('Error loading steps:', err);
    container.innerHTML = '<p>Failed to load steps.</p>';
  }
}

function renderSteps(steps) {
  const container = document.getElementById('steps');
  container.innerHTML = '';
  steps.forEach(step => {
    const div = document.createElement('div');
    div.classList.add('tutorial-step');
    div.innerHTML = `
      <h3>Step ${step.step_number}: ${escapeHTML(step.title)}</h3>
      <p>${escapeHTML(step.description)}</p>
    `;
    container.appendChild(div);
  });
}

function setupRealtime() {
  tutorialChannel = supabase
    .channel('public:tutorial_steps')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'tutorial_steps' }, async () => {
      await loadSteps();
    })
    .subscribe();
}

function setupProgressBar() {
  const container = document.getElementById('steps');
  const bar = document.getElementById('progress-bar');
  if (!container || !bar) return;
  container.addEventListener('scroll', () => {
    const percent = (container.scrollTop / (container.scrollHeight - container.clientHeight)) * 100;
    bar.style.width = `${percent}%`;
  });
}

function escapeHTML(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
