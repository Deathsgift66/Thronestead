/*
Project Name: Kingmakers Rise Frontend
File Name: signup.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", () => {
  // ✅ Bind form submit
  const form = document.getElementById('signup-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleSignup();
  });
});

// ✅ Handle Sign-Up
async function handleSignup() {
  const displayNameEl = document.getElementById('displayName');
  const usernameEl = document.getElementById('username');
  const emailEl = document.getElementById('email');
  const passwordEl = document.getElementById('password');
  const confirmPasswordEl = document.getElementById('confirmPassword');
  const agreeLegalEl = document.getElementById('agreeLegal');
  const toastEl = document.getElementById('toast');

  // ✅ Field Values
  const displayName = displayNameEl.value.trim();
  const username = usernameEl.value.trim();
  const email = emailEl.value.trim();
  const password = passwordEl.value;
  const confirmPassword = confirmPasswordEl.value;
  const agreed = agreeLegalEl.checked;

  // ✅ Validation
  if (!displayName || displayName.length < 3) {
    showToast("Display Name must be at least 3 characters.");
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
    display_name: displayName,
    username: username,
    email: email,
    password: password
  };

  try {
    // ✅ Simulate API Call — Replace with Supabase signUp when ready
    // const { data, error } = await supabase.auth.signUp({
    //   email: payload.email,
    //   password: payload.password,
    //   options: {
    //     data: {
    //       display_name: payload.display_name,
    //       username: payload.username
    //     }
    //   }
    // });

    // Temporary mock for now:
    console.log("🚀 Submitting sign-up payload:", payload);
    showToast("Sign-Up successful! Redirecting...");

    // ✅ Simulate successful redirect
    setTimeout(() => {
      window.location.href = 'play.html';
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

// ✅ Helper: Toast
function showToast(msg) {
  const toastEl = document.getElementById('toast');
  toastEl.textContent = msg;
  toastEl.classList.add("show");

  setTimeout(() => {
    toastEl.classList.remove("show");
  }, 3000);
}
