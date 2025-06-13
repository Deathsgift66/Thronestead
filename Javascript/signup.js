/*
Project Name: Kingmakers Rise Frontend
File Name: signup.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById('signup-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleSignup();
  });

  const kingdomNameEl = document.getElementById('kingdomName');
  const usernameEl = document.getElementById('username');

  const check = debounce(checkAvailability, 400);
  kingdomNameEl.addEventListener('input', check);
  usernameEl.addEventListener('input', check);

  loadSignupStats();
});

// ✅ Handle Sign-Up
async function handleSignup() {
  const kingdomNameEl = document.getElementById('kingdomName');
  const usernameEl = document.getElementById('username');
  const emailEl = document.getElementById('email');
  const passwordEl = document.getElementById('password');
  const confirmPasswordEl = document.getElementById('confirmPassword');
  const agreeLegalEl = document.getElementById('agreeLegal');
  const toastEl = document.getElementById('toast');

  // ✅ Field Values
  const kingdomName = kingdomNameEl.value.trim();
  const username = usernameEl.value.trim();
  const email = emailEl.value.trim();
  const password = passwordEl.value;
  const confirmPassword = confirmPasswordEl.value;
  const agreed = agreeLegalEl.checked;

  // ✅ Validation
  if (!kingdomName || kingdomName.length < 3) {
    showToast("Kingdom Name must be at least 3 characters.");
    return;
  }

  if (!username || username.length < 3) {
    showToast("Ruler Name must be at least 3 characters.");
    return;
  }

  if (!validateEmail(email)) {
    showToast("Invalid email address.");
    return;
  }

  if (password.length < 8) {
    showToast("Password must be at least 8 characters.");
    return;
  }

  if (!validatePasswordComplexity(password)) {
    showToast(
      "Password should contain at least one character of each: abcdefghijklmnopqrstuvwxyz, ABCDEFGHIJKLMNOPQRSTUVWXYZ, 0123456789, !@#$%^&*()_+-=[]{};':\"|<>?,./`~."
    );
    return;
  }

  if (password !== confirmPassword) {
    showToast("Passwords do not match.");
    return;
  }

  if (!agreed) {
    showToast("You must agree to the legal terms.");
    return;
  }

  // ✅ Payload
  const payload = {
    display_name: kingdomName,
    kingdom_name: kingdomName,
    username: username,
    email: email,
    password: password
  };

  try {
    const { data, error } = await supabase.auth.signUp({
      email: payload.email,
      password: payload.password,
      options: {
        data: {
          display_name: payload.display_name,
          username: payload.username
        }
      }
    });

    if (error) {
      throw new Error(error.message);
    }

    const userId = data?.user?.id;
    if (userId) {
      await fetch('/api/signup/create_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          username: payload.username,
          display_name: payload.display_name,
          kingdom_name: payload.kingdom_name,
          email: payload.email
        })
      });
    }

    showToast("Sign-Up successful! Redirecting to login...");
    setTimeout(() => {
      window.location.href = 'login.html';
    }, 1500);
  } catch (err) {
    console.error("❌ Sign-Up error:", err);
    showToast("Sign-Up failed. Please try again.");
  }
}

// ✅ Helper: Validate Email
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// ✅ Helper: Password Complexity
function validatePasswordComplexity(password) {
  const lower = /[a-z]/;
  const upper = /[A-Z]/;
  const digit = /[0-9]/;
  const special = /[!@#$%^&*()_+\-=[\]{};':"\\|<>?,./`~]/;
  return (
    lower.test(password) &&
    upper.test(password) &&
    digit.test(password) &&
    special.test(password)
  );
}

// ✅ Helper: Toast
function showToast(msg) {
  const toastEl = document.getElementById('toast');
  toastEl.textContent = msg;
  toastEl.classList.add("show");

  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
}

function debounce(fn, delay) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
}

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
    const kMsg = document.getElementById('kingdomName-msg');
    const uMsg = document.getElementById('username-msg');
    if (kingdom) {
      kMsg.textContent = data.kingdom_available ? 'Available' : 'Taken';
      kMsg.className = 'availability ' + (data.kingdom_available ? 'available' : 'taken');
    }
    if (user) {
      uMsg.textContent = data.username_available ? 'Available' : 'Taken';
      uMsg.className = 'availability ' + (data.username_available ? 'available' : 'taken');
    }
  } catch (err) {
    console.error('checkAvailability failed', err);
  }
}

async function loadSignupStats() {
  const panel = document.querySelector('.stats-panel');
  const list = document.getElementById('top-kingdoms-list');
  if (!panel || !list) return;
  try {
    const res = await fetch('/api/signup/stats');
    if (!res.ok) return;
    const data = await res.json();
    list.innerHTML = '';
    data.top_kingdoms.forEach(k => {
      const li = document.createElement('li');
      li.textContent = `${k.kingdom_name} - Power ${k.score}`;
      list.appendChild(li);
    });
    panel.classList.remove('hidden');
  } catch (err) {
    console.error('loadSignupStats failed', err);
  }
}
