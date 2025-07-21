import { supabase } from '../supabaseClient.js';
import { getEnvVar } from './env.js';
import { escapeHTML, formatDate } from './utils.js';

const API_BASE_URL = getEnvVar('API_BASE_URL');
let newsSub;

document.addEventListener('DOMContentLoaded', async () => {
  const url = new URL(window.location.href);
  const params = new URLSearchParams(url.hash.substring(1) || url.search);
  const accessToken = params.get('access_token');
  const type = params.get('type');

  if (accessToken || type === 'signup') {
    await supabase.auth.getSession();
    const { data: { session } } = await supabase.auth.getSession();
    url.hash = '';
    url.search = '';
    window.history.replaceState({}, document.title, url.pathname);
    if (session) {
      window.location.href = '/overview.html';
      return;
    }
    window.location.href = '/login.html';
    return;
  }

  enableSmoothScroll();
  await updateHeroCTA();
  setupFloatingCTA();
  await loadNews();
  setupNewsRealtime();
});

async function updateHeroCTA() {
  const { data: { session } } = await supabase.auth.getSession();
  const heroButton = document.querySelector('.hero-buttons a');
  const ctaButton = document.querySelector('.cta-section a');

  if (heroButton) {
    heroButton.textContent = session ? 'Play Now' : 'Join the Realm';
    heroButton.href = session ? 'play.html' : 'signup.html';
  }

  if (ctaButton) {
    ctaButton.textContent = session ? 'Continue Kingdom' : 'Create Your Kingdom';
    ctaButton.href = session ? 'play.html' : 'signup.html';
  }
}

function enableSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

function setupFloatingCTA() {
  const ctaSection = document.querySelector('.cta-section');
  if (!ctaSection) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
      ctaSection.classList.add('sticky');
    } else {
      ctaSection.classList.remove('sticky');
    }
  });
}

async function loadNews() {
  const list = document.getElementById('news-list');
  if (!list) return;
  list.setAttribute('aria-busy', 'true');

  try {
    const res = await fetch(`${API_BASE_URL}/api/homepage/featured`);
    const data = await res.json();
    list.innerHTML = '';
    list.removeAttribute('aria-busy');

    if (!data.articles?.length) {
      list.innerHTML = '<li>No news available.</li>';
      return;
    }

    data.articles.forEach(a => {
      const li = document.createElement('li');
      li.innerHTML = `
        <strong>${escapeHTML(a.title)}</strong>
        <span class="date">${escapeHTML(formatDate(a.published_at))}</span><br>
        ${escapeHTML(a.summary)}
      `;
      list.appendChild(li);
    });
  } catch (err) {
    console.error('❌ Error loading news:', err);
    list.innerHTML = '<li>Failed to load news.</li>';
    list.removeAttribute('aria-busy');
  }
}

function setupNewsRealtime() {
  const list = document.getElementById('news-list');
  if (!list) return;
  newsSub = supabase
    .channel('news_articles')
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'news_articles'
    }, async () => {
      await loadNews();
    })
    .subscribe();
}

window.addEventListener('beforeunload', () => {
  newsSub?.unsubscribe();
});

document.addEventListener('DOMContentLoaded', setupDonationLink);

function setupDonationLink() {
  const container = document.getElementById('donate-container');
  if (!container) return;
  const btn = document.createElement('button');
  btn.className = 'cta-button';
  btn.textContent = 'Donate';
  btn.addEventListener('click', () => {
    const answer = prompt('What is 3 + 4?');
    if (answer === null) return;
    if (parseInt(answer, 10) === 7) {
      window.location.href = atob('aHR0cHM6Ly93d3cucGF5cGFsLmNvbS9uY3AvcGF5bWVudC9ZQjRMVzdYUkVMSkJT');
    } else {
      alert('Incorrect answer. Please try again.');
    }
  });
  container.appendChild(btn);
}
