/*
Project Name: Kingmakers Rise Frontend
File Name: news.js
Date: June 2, 2025
Author: Deathsgift66
*/
// Dynamic News Hub — Article Listing

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Initial load
  await loadNewsArticles();
});

// ✅ Load News Articles
async function loadNewsArticles() {
  const container = document.querySelector(".content-container");

  container.innerHTML = "<p>Loading news articles...</p>";

  try {
    const res = await fetch("/api/news/articles");
    const data = await res.json();

    container.innerHTML = "";

    if (!data.articles || data.articles.length === 0) {
      container.innerHTML = "<p>No news articles found.</p>";
      return;
    }

    data.articles.forEach(article => {
      const card = document.createElement("div");
      card.classList.add("news-article-card");

      card.innerHTML = `
        <h3>${escapeHTML(article.title)}</h3>
        <p class="news-meta">By ${escapeHTML(article.author_name)} — ${formatDate(article.published_at)}</p>
        <p class="news-summary">${escapeHTML(article.summary)}</p>
        <a href="news_article.html?article_id=${article.article_id}" class="action-btn">Read More</a>
      `;

      container.appendChild(card);
    });

  } catch (err) {
    console.error("❌ Error loading news articles:", err);
    container.innerHTML = "<p>Failed to load news articles.</p>";
  }
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
