// Project Name: Thronestead©
// File Name: town_criers.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML, showToast } from './utils.js';
import { setupTabs } from './components/tabControl.js';

let scrollChannel = null;

document.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  await Promise.all([
    loadBoard(),
    loadYourScrolls()
  ]);
  subscribeToScrolls();

  const composeForm = document.getElementById('compose-form');
  composeForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitScroll();
  });
});

// ✅ UI Tabs Handler

// ✅ Load Global Bulletin
async function loadBoard() {
  const boardEl = document.getElementById('board-feed');
  boardEl.innerHTML = "<p>Loading board feed...</p>";

  try {
    const { data: { session } } = await supabase.auth.getSession();
    const res = await fetch('/api/town-criers/latest', {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        'X-User-ID': session.user.id
      }
    });
    const { scrolls = [] } = await res.json();

    boardEl.innerHTML = scrolls.length
      ? scrolls.map(renderScrollCard).join('')
      : "<p>No scrolls posted yet.</p>";

  } catch (err) {
    console.error("❌ Board Feed Error:", err);
    showToast("Failed to load board feed.");
  }
}

// ✅ Load Personal Scrolls
async function loadYourScrolls() {
  const yourEl = document.getElementById('your-scrolls');
  yourEl.innerHTML = "<p>Loading your scrolls...</p>";

  try {
    const { data: { user } } = await supabase.auth.getUser();
    const { data = [], error } = await supabase
      .from('town_crier_scrolls')
      .select('*')
      .eq('author_id', user.id)
      .order('created_at', { ascending: false });

    if (error) throw error;

    yourEl.innerHTML = data.length
      ? data.map(renderScrollCard).join('')
      : "<p>You have not posted any scrolls yet.</p>";

  } catch (err) {
    console.error("❌ Your Scrolls Error:", err);
    showToast("Failed to load your scrolls.");
  }
}

// ✅ Scroll Card Renderer
function renderScrollCard(scroll) {
  const author = escapeHTML(scroll.author_display_name || 'Unknown');
  const title = escapeHTML(scroll.title);
  const body = escapeHTML(scroll.body);
  const date = new Date(scroll.created_at).toLocaleString();

  return `
    <div class="scroll-card">
      <h4>${title}</h4>
      <p>${body}</p>
      <small>Posted by: ${author} • ${date}</small>
    </div>
  `;
}

// ✅ Real-Time Subscription
function subscribeToScrolls() {
  scrollChannel = supabase
    .channel('public:town_crier_scrolls')
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'town_crier_scrolls'
    }, loadBoard)
    .subscribe();

  window.addEventListener('beforeunload', () => {
    if (scrollChannel) supabase.removeChannel(scrollChannel);
  });
}

// ✅ Submit New Scroll
async function submitScroll() {
  const titleEl = document.getElementById('scroll-title');
  const bodyEl = document.getElementById('scroll-body');
  const title = titleEl.value.trim();
  const body = bodyEl.value.trim();

  if (title.length < 3) return showToast("Title must be at least 3 characters.");
  if (body.length < 10) return showToast("Body must be at least 10 characters.");

  try {
    const { data: { session } } = await supabase.auth.getSession();
    const res = await fetch('/api/town-criers/post', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`,
        'X-User-ID': session.user.id
      },
      body: JSON.stringify({ title, body })
    });

    if (!res.ok) {
      const { detail } = await res.json();
      throw new Error(detail || "Failed");
    }

    showToast("Scroll posted successfully!");
    titleEl.value = "";
    bodyEl.value = "";

    await Promise.all([
      loadBoard(),
      loadYourScrolls()
    ]);

  } catch (err) {
    console.error("❌ Submit Scroll Error:", err);
    showToast("Failed to submit scroll.");
  }
}
