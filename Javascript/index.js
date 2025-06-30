// Project Name: Thronestead©
// File Name: index.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || window.env?.API_BASE_URL || '';

document.addEventListener("DOMContentLoaded", async () => {
  enableSmoothScroll();        // ✅ Smooth scrolling behavior
  await updateHeroCTA();       // ✅ Dynamic CTA buttons
  setupFloatingCTA();          // ✅ Sticky CTA on scroll
  await loadNews();            // ✅ Load featured news
  setupNewsRealtime();         // ✅ Sub to real-time news updates
});

// =============================
// 🔁 Dynamic CTA Button Binding
// =============================
async function updateHeroCTA() {
  const { data: { session } } = await supabase.auth.getSession();
  const heroButton = document.querySelector(".hero-buttons a");
  const ctaButton = document.querySelector(".cta-section a");

  if (heroButton) {
    heroButton.textContent = session ? "Play Now" : "Join the Realm";
    heroButton.href = session ? "play.html" : "signup.html";
  }

  if (ctaButton) {
    ctaButton.textContent = session ? "Continue Kingdom" : "Create Your Kingdom";
    ctaButton.href = session ? "play.html" : "signup.html";
  }
}

// =============================
// 📜 Smooth Scroll for Anchors
// =============================
function enableSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
}

// =============================
// 📌 Sticky CTA on Scroll
// =============================
function setupFloatingCTA() {
  const ctaSection = document.querySelector(".cta-section");
  if (!ctaSection) return;

  window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
      ctaSection.classList.add("sticky");
    } else {
      ctaSection.classList.remove("sticky");
    }
  });
}

// =============================
// 📰 Load Homepage News
// =============================
async function loadNews() {
  const list = document.getElementById("news-list");
  if (!list) return;
  list.innerHTML = "<li>Loading news...</li>";

  try {
    const res = await fetch(`${API_BASE_URL}/api/homepage/featured`);
    const data = await res.json();
    list.innerHTML = "";

    if (!data.articles?.length) {
      list.innerHTML = "<li>No news available.</li>";
      return;
    }

    data.articles.forEach(a => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${escapeHTML(a.title)}</strong> 
        <span class="date">${formatDate(a.published_at)}</span><br>
        ${escapeHTML(a.summary)}
      `;
      list.appendChild(li);
    });
  } catch (err) {
    console.error("❌ Error loading news:", err);
    list.innerHTML = "<li>Failed to load news.</li>";
  }
}

// =============================
// 🔁 Supabase Realtime Sync
// =============================
let newsSub;
function setupNewsRealtime() {
  const list = document.getElementById("news-list");
  if (!list) return;
  newsSub = supabase
    .channel("news_articles")
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'news_articles'
    }, async () => {
      await loadNews(); // Live reload on new post
    })
    .subscribe();
}

// =============================
// 🧹 Clean up on unload
// =============================
window.addEventListener('beforeunload', () => {
  newsSub?.unsubscribe();
});

// =============================
// 📅 Format Date to Friendly Text
// =============================
function formatDate(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// =============================
// 💖 Donate Link Handler
// =============================
document.addEventListener('DOMContentLoaded', setupDonationLink);

function setupDonationLink() {
  const container = document.getElementById('donate-container');
  if (!container) return;
  const btn = document.createElement('button');
  btn.className = 'cta-button';
  btn.textContent = 'Donate';
  btn.addEventListener('click', () => {
    const answer = prompt('What is 3 + 4?');
    if (answer === null) return; // user cancelled prompt
    if (parseInt(answer, 10) === 7) {
      window.location.href = atob('aHR0cHM6Ly93d3cucGF5cGFsLmNvbS9uY3AvcGF5bWVudC9ZQjRMVzdYUkVMSkJT');
    } else {
      alert('Incorrect answer. Please try again.');
    }
  });
  container.appendChild(btn);
}

// =============================
// 🛡️ Basic HTML Escaping
// =============================
