// Project Name: Thronestead©
// File Name: tutorial.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';

let currentUser = null;
let tutorialChannel;

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) return (window.location.href = "login.html");
  currentUser = session.user;

  await loadSteps();
  setupRealtime();
  initScrollAnimations();
  setupProgressBar();
});

// ✅ Smooth fade-in animation for tutorial steps
function initScrollAnimations() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      entry.target.classList.toggle('visible', entry.isIntersecting);
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.tutorial-step').forEach(step => observer.observe(step));
}

// ✅ Load tutorial steps from API
async function loadSteps() {
  const container = document.getElementById('steps');
  container.innerHTML = '<p>📜 Loading tutorial steps...</p>';
  try {
    const res = await fetch('/api/tutorial/steps', {
      headers: { 'X-User-ID': currentUser.id }
    });
    const { steps } = await res.json();
    renderSteps(steps || []);
  } catch (err) {
    console.error('❌ Error loading tutorial steps:', err);
    container.innerHTML = `<p>⚠️ Failed to load steps. <button onclick="location.reload()">Retry</button></p>`;
  }
}

// ✅ Render steps into DOM
function renderSteps(steps) {
  const container = document.getElementById('steps');
  container.innerHTML = '';

  steps.forEach(step => {
    const div = document.createElement('div');
    div.className = 'tutorial-step';
    div.setAttribute('tabindex', '0');
    div.setAttribute('role', 'region');
    div.setAttribute('aria-label', `Tutorial Step ${step.step_number}: ${step.title}`);

    div.innerHTML = `
      <h3>Step ${step.step_number}: ${escapeHTML(step.title)}</h3>
      <p>${escapeHTML(step.description)}</p>
    `;
    container.appendChild(div);
  });

  // Scroll to top when reloaded
  container.scrollTo({ top: 0, behavior: 'smooth' });
}

// ✅ Subscribe to live tutorial step updates
function setupRealtime() {
  tutorialChannel = supabase
    .channel('public:tutorial_steps')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'tutorial_steps'
    }, async () => {
      await loadSteps();
    })
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (tutorialChannel) supabase.removeChannel(tutorialChannel);
  });
}

// ✅ Progress bar tracker
function setupProgressBar() {
  const container = document.getElementById('steps');
  const bar = document.getElementById('progress-bar');
  if (!container || !bar) return;

  let ticking = false;
  container.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const percent = (container.scrollTop / (container.scrollHeight - container.clientHeight)) * 100;
        bar.style.width = `${percent.toFixed(1)}%`;
        ticking = false;
      });
      ticking = true;
    }
  });
}

// ✅ Safe HTML escape
