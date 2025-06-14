// Project Name: Kingmakers Rise©
// File Name: signup.js
// Version 6.14.2025.20.12
// Developer: Deathsgift66
import { showToast, validateEmail, debounce } from './utils.js';
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById('signup-form');
  const kingdomNameEl = document.getElementById('kingdomName');
  const usernameEl = document.getElementById('username');

  // ✅ Debounced availability checker
  const check = debounce(checkAvailability, 400);
  kingdomNameEl.addEventListener('input', check);
  usernameEl.addEventListener('input', check);

  // ✅ Bind form submit
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleSignup();
  });

  // ✅ Show top kingdoms for social proof
  loadSignupStats();
});

// ✅ Signup flow handler
async function handleSignup() {
  const values = {
    kingdomName: document.getElementById('kingdomName').value.trim(),
    username: document.getElementById('username').value.trim(),
    email: document.getElementById('email').value.trim(),
    password: document.getElementById('password').value,
    confirmPassword: document.getElementById('confirmPassword').value,
    agreed: document.getElementById('agreeLegal').checked
  };

  // ✅ Input validations
  if (values.kingdomName.length < 3) return showToast("Kingdom Name must be at least 3 characters.");
  if (values.username.length < 3) return showToast("Ruler Name must be at least 3 characters.");
  if (!validateEmail(values.email)) return showToast("Invalid email address.");
  if (values.password.length < 8) return showToast("Password must be at least 8 characters.");
  if (!validatePasswordComplexity(values.password)) {
    return showToast("Password must include lowercase, uppercase, number, and symbol.");
  }
  if (values.password !== values.confirmPassword) return showToast("Passwords do not match.");
  if (!values.agreed) return showToast("You must agree to the legal terms.");

  // ✅ Submit registration
  const payload = {
    display_name: values.kingdomName,
    kingdom_name: values.kingdomName,
    username: values.username,
    email: values.email,
    password: values.password
  };

  try {
    const res = await fetch('/api/signup/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }

    showToast("Sign-Up successful! Redirecting to login...");
    setTimeout(() => (window.location.href = 'login.html'), 1500);
  } catch (err) {
    console.error("❌ Sign-Up error:", err);
    showToast("Sign-Up failed. Please try again.");
  }
}

// ✅ Realtime check name availability
async function checkAvailability() {
  const kingdom = document.getElementById('kingdomName').value.trim();
  const user = document.getElementById('username').value.trim();
  if (!kingdom && !user) return;

  try {
    const res = await fetch('/api/signup/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kingdom_name: kingdom, username: user })
    });

    if (!res.ok) return;
    const data = await res.json();
    updateAvailabilityUI('kingdomName-msg', data.kingdom_available);
    updateAvailabilityUI('username-msg', data.username_available);
  } catch (err) {
    console.error("Availability check failed", err);
  }
}

function updateAvailabilityUI(id, available) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = available ? "Available" : "Taken";
  el.className = 'availability ' + (available ? 'available' : 'taken');
}

// ✅ Load top kingdom list (social proof)
async function loadSignupStats() {
  const panel = document.querySelector('.stats-panel');
  const list = document.getElementById('top-kingdoms-list');
  if (!panel || !list) return;

  try {
    const res = await fetch('/api/signup/stats');
    if (!res.ok) return;
    const data = await res.json();
    list.innerHTML = "";

    (data.top_kingdoms || []).forEach(k => {
      const li = document.createElement('li');
      li.textContent = `${k.kingdom_name} — Power ${k.score}`;
      list.appendChild(li);
    });

    panel.classList.remove('hidden');
  } catch (err) {
    console.error("Stats fetch failed", err);
  }
}
