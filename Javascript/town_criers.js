/*
Project Name: Kingmakers Rise Frontend
File Name: town_criers.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js protects this page → no duplicate session check
  initTabs();
  await loadBoard();
  await loadYourScrolls();

  // ✅ Bind compose form
  const composeForm = document.getElementById('compose-form');
  composeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitScroll();
  });
});

// ✅ Tabs
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabSections = document.querySelectorAll('.tab-section');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-target');

      tabButtons.forEach(b => b.classList.remove('active'));
      tabSections.forEach(section => section.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(target).classList.add('active');
    });
  });
}

// ✅ Load Board Feed
async function loadBoard() {
  const boardEl = document.getElementById('board-feed');
  boardEl.innerHTML = "<p>Loading board feed...</p>";

  try {
    const { data, error } = await supabase
      .from('town_crier_scrolls')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(25);

    if (error) throw error;

    boardEl.innerHTML = "";

    if (data.length === 0) {
      boardEl.innerHTML = "<p>No scrolls posted yet.</p>";
      return;
    }

    data.forEach(scroll => {
      const card = document.createElement("div");
      card.classList.add("scroll-card");

      card.innerHTML = `
        <h4>${escapeHTML(scroll.title)}</h4>
        <p>${escapeHTML(scroll.body)}</p>
        <small>Posted by: ${escapeHTML(scroll.author_display_name || 'Unknown')} • ${new Date(scroll.created_at).toLocaleString()}</small>
      `;

      boardEl.appendChild(card);
    });

  } catch (err) {
    console.error("❌ Error loading board feed:", err);
    showToast("Failed to load board feed.");
  }
}

// ✅ Load Your Scrolls
async function loadYourScrolls() {
  const yourEl = document.getElementById('your-scrolls');
  yourEl.innerHTML = "<p>Loading your scrolls...</p>";

  try {
    const { data: { user } } = await supabase.auth.getUser();

    const { data, error } = await supabase
      .from('town_crier_scrolls')
      .select('*')
      .eq('author_id', user.id)
      .order('created_at', { ascending: false });

    if (error) throw error;

    yourEl.innerHTML = "";

    if (data.length === 0) {
      yourEl.innerHTML = "<p>You have not posted any scrolls yet.</p>";
      return;
    }

    data.forEach(scroll => {
      const card = document.createElement("div");
      card.classList.add("scroll-card");

      card.innerHTML = `
        <h4>${escapeHTML(scroll.title)}</h4>
        <p>${escapeHTML(scroll.body)}</p>
        <small>Posted: ${new Date(scroll.created_at).toLocaleString()}</small>
      `;

      yourEl.appendChild(card);
    });

  } catch (err) {
    console.error("❌ Error loading your scrolls:", err);
    showToast("Failed to load your scrolls.");
  }
}

// ✅ Submit Scroll
async function submitScroll() {
  const titleEl = document.getElementById('scroll-title');
  const bodyEl = document.getElementById('scroll-body');

  const title = titleEl.value.trim();
  const body = bodyEl.value.trim();

  if (!title || title.length < 3) {
    showToast("Title must be at least 3 characters.");
    return;
  }

  if (!body || body.length < 10) {
    showToast("Body must be at least 10 characters.");
    return;
  }

  try {
    const { data: { user } } = await supabase.auth.getUser();

    const { data: profile, error: profileError } = await supabase
      .from('users')
      .select('display_name')
      .eq('user_id', user.id)
      .single();

    if (profileError) throw profileError;

    const payload = {
      author_id: user.id,
      author_display_name: profile.display_name,
      title: title,
      body: body
    };

    const { error } = await supabase
      .from('town_crier_scrolls')
      .insert(payload);

    if (error) throw error;

    showToast("Scroll posted successfully!");

    // Clear form
    titleEl.value = "";
    bodyEl.value = "";

    // Reload feeds
    await loadBoard();
    await loadYourScrolls();

  } catch (err) {
    console.error("❌ Error submitting scroll:", err);
    showToast("Failed to submit scroll.");
  }
}

// ✅ Helper: Toast
function showToast(msg) {
  let toastEl = document.getElementById('toast');

  // Inject toast if not present
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.id = "toast";
    toastEl.className = "toast-notification";
    document.body.appendChild(toastEl);
  }

  toastEl.textContent = msg;
  toastEl.classList.add("show");

  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
}

// ✅ Helper: Escape HTML
function escapeHTML(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
