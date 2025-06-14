// Project Name: Kingmakers Rise©
// File Name: news.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';

let currentUser = null;
let newsChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  currentUser = session.user;

  await loadNewsArticles();
  setupRealtime();

  const search = document.getElementById('search-input');
  if (search) {
    search.addEventListener('input', filterArticles);
  }
});

// ✅ Load News Articles
async function loadNewsArticles() {
  const container = document.getElementById('articles');
  if (!container) return;

  container.innerHTML = "<p>Loading news articles...</p>";

  try {
    const res = await fetch("/api/news/articles", {
      headers: { 'X-User-ID': currentUser.id }
    });

    if (!res.ok) throw new Error(`Failed to load news. Code: ${res.status}`);
    const data = await res.json();

    renderArticles(data.articles || []);
  } catch (err) {
    console.error("❌ Error loading news articles:", err);
    container.innerHTML = "<p>Failed to load news articles.</p>";
  }
}

// ✅ Render News Cards
function renderArticles(articles) {
  const container = document.getElementById('articles');
  if (!container) return;

  container.innerHTML = '';

  if (!articles.length) {
    container.innerHTML = '<p>No news articles found.</p>';
    return;
  }

  articles.forEach(article => {
    const card = document.createElement('div');
    card.classList.add('news-article-card');
    card.dataset.title = (article.title || '').toLowerCase();
    card.dataset.summary = (article.summary || '').toLowerCase();

    card.innerHTML = `
      <h3>${escapeHTML(article.title)}</h3>
      <p class="news-meta">By ${escapeHTML(article.author_name || "System")} — ${formatDate(article.published_at)}</p>
      <p class="news-summary">${escapeHTML(article.summary || "")}</p>
      <a href="#" class="action-btn" title="Full article page coming soon">Read More</a>
    `;

    container.appendChild(card);
  });
}

// ✅ Search Filter
function filterArticles() {
  const searchEl = document.getElementById('search-input');
  const term = searchEl ? searchEl.value.toLowerCase() : '';

  document.querySelectorAll('.news-article-card').forEach(card => {
    const match = card.dataset.title.includes(term) || card.dataset.summary.includes(term);
    card.style.display = match ? '' : 'none';
  });
}

// ✅ Real-time Sync via Supabase
function setupRealtime() {
  newsChannel = supabase
    .channel('public:news_articles')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'news_articles' },
      async () => {
        await loadNewsArticles();
      }
    )
    .subscribe(status => {
      const indicator = document.getElementById("realtime-indicator");
      if (indicator) {
        if (status === "SUBSCRIBED") {
          indicator.textContent = "Live";
          indicator.className = "connected";
        } else {
          indicator.textContent = "Offline";
          indicator.className = "disconnected";
        }
      }
    });

  window.addEventListener("beforeunload", () => {
    if (newsChannel) supabase.removeChannel(newsChannel);
  });
}

// ✅ Format Date
function formatDate(ts) {
  if (!ts) return "Unknown";
  const date = new Date(ts);
  return date.toLocaleDateString(undefined, {
    year: "numeric", month: "short", day: "numeric"
  });
}

// ✅ Basic HTML Escape
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
