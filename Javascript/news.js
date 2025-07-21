// Project Name: Thronestead©
// File Name: news.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import {
  openModal,
  closeModal,
  sanitizeHTML,
  relativeTime
} from './utils.js';

let newsChannel = null;
let offset = 0;
const pageSize = 20;

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
  document.getElementById('load-more-btn')?.addEventListener('click', () => loadNews(true));

  // Close button for modal
  document.getElementById('close-article-btn')?.addEventListener('click', hideArticleModal);
});

// ✅ Load News Articles
async function loadNews(append = false) {
  const articleGrid = document.getElementById('articles');
  const loadingIndicator = document.getElementById('loading-news');
  const noResultsMsg = document.getElementById('no-results-message');
  const loadMoreBtn = document.getElementById('load-more-btn');

  if (!articleGrid || !loadingIndicator || !noResultsMsg) return;

  loadingIndicator.style.display = 'block';
  if (!append) {
    noResultsMsg.classList.add('hidden');
    articleGrid.innerHTML = '';
    offset = 0;
  }

  const { data: articles, error } = await supabase
    .from('announcements')
    .select('*')
    .eq('visible', true)
    .order('created_at', { ascending: false })
    .range(offset, offset + pageSize - 1);

  loadingIndicator.style.display = 'none';

  if (error || !articles || articles.length === 0) {
    if (!append) noResultsMsg.classList.remove('hidden');
    loadMoreBtn?.classList.add('hidden');
    return;
  }

  offset += articles.length;
  renderArticles(articles, append);
  if (articles.length < pageSize) loadMoreBtn?.classList.add('hidden');
  else loadMoreBtn?.classList.remove('hidden');
}

// ✅ Render News Cards
function renderArticles(articles, append = true) {
  const container = document.getElementById('articles');
  const template = document.getElementById('article-template');
  if (!container || !template) return;

  if (!append) container.innerHTML = '';

  articles.forEach(article => {
    const clone = template.content.firstElementChild.cloneNode(true);
    clone.classList.add('news-article-card');
    clone.dataset.title = (article.title || '').toLowerCase();
    clone.dataset.summary = (article.content || '').toLowerCase();
    clone.querySelector('.article-title').textContent = article.title;
    const snippet = article.content.replace(/<[^>]*>/g, '').slice(0, 140);
    clone.querySelector('.article-summary').textContent = `${snippet}...`;
    clone.querySelector('.article-meta').textContent = relativeTime(article.created_at);
    clone.addEventListener('click', () => showArticleModal(article));
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
function showArticleModal(article) {
  const modal = document.getElementById('article-modal');
  if (!modal) return;
  modal.querySelector('#article-title').textContent = article.title || 'Untitled';
  modal.querySelector('#article-meta').textContent = relativeTime(article.created_at);
  let html = article.content;
  if (window.marked) {
    html = window.marked.parse(article.content);
  }
  modal.querySelector('#article-body').innerHTML = sanitizeHTML(html);
  openModal('article-modal');
}

function hideArticleModal() {
  closeModal('article-modal');
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') hideArticleModal();
});
