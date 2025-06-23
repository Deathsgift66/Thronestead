// Project Name: Thronestead©
// File Name: news.js
// Version 6.15.2025.00.00
// Developer: Codex
import { supabase } from '../supabaseClient.js';
import { formatDate } from './utils.js';

let newsChannel = null;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }

  await loadNews();
  setupRealtime();

  const search = document.getElementById('search-input');
  if (search) search.addEventListener('input', filterArticles);

  // Close button for modal
  document.getElementById('close-article-btn')?.addEventListener('click', closeModal);
});

// ✅ Load News Articles
async function loadNews() {
  const articleGrid = document.getElementById('articles');
  const loadingIndicator = document.getElementById('loading-news');
  const noResultsMsg = document.getElementById('no-results-message');

  if (!articleGrid || !loadingIndicator || !noResultsMsg) return;

  loadingIndicator.style.display = 'block';
  noResultsMsg.classList.add('hidden');
  articleGrid.innerHTML = '';

  const { data: articles, error } = await supabase
    .from('announcements')
    .select('*')
    .eq('visible', true)
    .order('created_at', { ascending: false })
    .limit(50);

  loadingIndicator.style.display = 'none';

  if (error || !articles || articles.length === 0) {
    noResultsMsg.classList.remove('hidden');
    return;
  }

  renderArticles(articles);
}

// ✅ Render News Cards
function renderArticles(articles) {
  const container = document.getElementById('articles');
  const template = document.getElementById('article-template');
  if (!container || !template) return;

  container.innerHTML = '';

  articles.forEach(article => {
    const clone = template.content.firstElementChild.cloneNode(true);
    clone.classList.add('news-article-card');
    clone.dataset.title = (article.title || '').toLowerCase();
    clone.dataset.summary = (article.content || '').toLowerCase();
    clone.querySelector('.article-title').textContent = article.title;
    clone.querySelector('.article-summary').textContent = `${article.content.slice(0, 140)}...`;
    clone.querySelector('.article-meta').textContent = formatDate(article.created_at);
    clone.addEventListener('click', () => openModal(article));
    container.appendChild(clone);
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
    .channel('news-hub')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'announcements' }, () => loadNews())
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (newsChannel) supabase.removeChannel(newsChannel);
  });
}

// ✅ Modal viewer for full article
function openModal(article) {
  const modal = document.getElementById('article-modal');
  if (!modal) return;
  modal.querySelector('#article-title').textContent = article.title || 'Untitled';
  modal.querySelector('#article-meta').textContent = formatDate(article.created_at);
  modal.querySelector('#article-body').innerHTML = article.content;
  modal.classList.remove('hidden');
}

function closeModal() {
  document.getElementById('article-modal')?.classList.add('hidden');
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});
