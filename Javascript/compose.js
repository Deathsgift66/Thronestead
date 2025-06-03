// compose.js — FINAL AAA/SSS VERSION — 6.2.25
// Hardened Compose Message Page

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ Bind logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await supabase.auth.signOut();
      window.location.href = "login.html";
    });
  }

  // ✅ Validate session
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = "login.html";
    return;
  }

  // ✅ Bind compose form
  const composeForm = document.getElementById("compose-form");
  if (composeForm) {
    composeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await sendMessage();
    });
  }
});

// ✅ Send Message
async function sendMessage() {
  const recipient = document.getElementById("recipient").value.trim();
  const content = document.getElementById("message-content").value.trim();

  if (!recipient || !content) {
    alert("Please enter both recipient and message content.");
    return;
  }

  try {
    const res = await fetch("/api/messages/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipient, content })
    });

    const result = await res.json();

    if (!res.ok) {
      throw new Error(result.error || "Failed to send message.");
    }

    alert(result.message || "Message sent successfully!");
    window.location.href = "messages.html";

  } catch (err) {
    console.error("❌ Error sending message:", err);
    alert("Failed to send message. Please try again.");
  }
}
