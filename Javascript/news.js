/*
Project Name: Kingmakers Rise Frontend
File Name: news.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Dynamic News Hub — Article Listing

import { supabase } from './supabaseClient.js';

let currentUser = null;
let newsChannel;

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

  container.innerHTML = "<p>Loading news articles...</p>";

  try {
    const res = await fetch("/api/news/articles", {
      headers: { 'X-User-Id': currentUser.id }
    });
    const data = await res.json();

    renderArticles(data.articles || []);

  } catch (err) {
    console.error("❌ Error loading news articles:", err);
    container.innerHTML = "<p>Failed to load news articles.</p>";
  }
}

function renderArticles(articles) {
  const container = document.getElementById('articles');
  container.innerHTML = '';
  if (!articles.length) {
    container.innerHTML = '<p>No news articles found.</p>';
    return;
  }
  articles.forEach(article => {
    const card = document.createElement('div');
    card.classList.add('news-article-card');
    card.dataset.title = (article.title || '').toLowerCase();
    card.innerHTML = `
      <h3>${escapeHTML(article.title)}</h3>
      <p class="news-meta">By ${escapeHTML(article.author_name)} — ${formatDate(article.published_at)}</p>
      <p class="news-summary">${escapeHTML(article.summary)}</p>
      <a href="news_article.html?article_id=${article.article_id}" class="action-btn">Read More</a>
    `;
    container.appendChild(card);
  });
}

function filterArticles() {
  const term = document.getElementById('search-input').value.toLowerCase();
  document.querySelectorAll('.news-article-card').forEach(card => {
    card.style.display = card.dataset.title.includes(term) ? '' : 'none';
  });
}

function setupRealtime() {
  newsChannel = supabase
    .channel('public:news_articles')
    .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'news_articles' }, () => loadNewsArticles())
    .subscribe();
}

// ✅ Date formatting
function formatDate(ts) {
  if (!ts) return "Unknown";
  const date = new Date(ts);
  return date.toLocaleDateString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit"
  });
}

// ✅ Basic HTML escape
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
