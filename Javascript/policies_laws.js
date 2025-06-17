// Project Name: Thronestead©
// File Name: policies_laws.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
import { supabase } from './supabaseClient.js';
import { escapeHTML, debounce } from './utils.js';

document.addEventListener("DOMContentLoaded", async () => {
  await loadPoliciesAndLaws();
});

// ✅ Load Policies and Laws
async function loadPoliciesAndLaws() {
  const policyContainer = document.querySelector(".policy-options");
  const lawContainer = document.querySelector(".law-options");
  const summaryContainer = document.getElementById("summary-content");

  policyContainer.innerHTML = "<p>Loading policies...</p>";
  lawContainer.innerHTML = "<p>Loading laws...</p>";
  summaryContainer.innerHTML = "<p>Building summary...</p>";

  try {
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    const uid = session?.user?.id;

    const headers = {
      'Authorization': `Bearer ${token}`,
      'X-User-ID': uid,
      'Content-Type': 'application/json'
    };

    const userRes = await fetch('/api/policies-laws/user', { headers });
    const userData = await userRes.json();

    const activePolicy = userData.active_policy;
    const activeLaws = userData.active_laws || [];

    const catRes = await fetch('/api/policies-laws/catalogue', { headers });
    const { entries: catalogData } = await catRes.json();

    const policies = catalogData.filter(e => e.type === "policy");
    const laws = catalogData.filter(e => e.type === "law");

    policyContainer.innerHTML = "";
    lawContainer.innerHTML = "";

    // 🔹 Render Policies
    for (const policy of policies) {
      const card = document.createElement("div");
      card.className = "policy-card";
      if (policy.id === activePolicy) card.classList.add("active-policy");

      card.innerHTML = `
        <span class="glow"></span>
        <h3>${escapeHTML(policy.name)}</h3>
        <p>${escapeHTML(policy.description)}</p>
        <p><strong>Category:</strong> ${escapeHTML(policy.category)}</p>
        <p><strong>Unlock:</strong> Castle Lvl ${policy.unlock_at_level}</p>
        <p><strong>Effect:</strong> ${escapeHTML(policy.effect_summary)}</p>
        <button class="action-btn policy-select-btn" data-id="${policy.id}">Select</button>
      `;
      policyContainer.appendChild(card);
    }

    // 🔹 Render Laws
    for (const law of laws) {
      const card = document.createElement("div");
      card.className = "law-card";

      const isActive = activeLaws.includes(law.id);

      card.innerHTML = `
        <span class="glow"></span>
        <h3>${escapeHTML(law.name)}</h3>
        <p>${escapeHTML(law.description)}</p>
        <p><strong>Category:</strong> ${escapeHTML(law.category)}</p>
        <p><strong>Unlock:</strong> Castle Lvl ${law.unlock_at_level}</p>
        <p><strong>Effect:</strong> ${escapeHTML(law.effect_summary)}</p>
        <label><input type="checkbox" class="law-toggle" data-id="${law.id}" ${isActive ? "checked" : ""}> Active</label>
      `;
      lawContainer.appendChild(card);
    }

    // 🔘 Bind policy selectors
    document.querySelectorAll(".policy-select-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const policyId = parseInt(btn.dataset.id);
        btn.disabled = true;
        try {
          const res = await fetch('/api/policies-laws/policy', {
            method: 'POST',
            headers,
            body: JSON.stringify({ policy_id: policyId })
          });
          if (!res.ok) throw new Error('Policy change failed');
          alert("✅ Policy updated!");
          await loadPoliciesAndLaws();
        } catch (err) {
          console.error("❌", err);
          alert("Failed to change policy.");
        } finally {
          btn.disabled = false;
        }
      });
    });

    // 🔘 Bind law toggles with debounce
    const debouncedUpdate = debounce(() => updateLawToggles(headers), 300);
    document.querySelectorAll(".law-toggle").forEach(toggle => {
      toggle.addEventListener("change", debouncedUpdate);
    });

    updateSummary(activePolicy, activeLaws, policies, laws);

  } catch (err) {
    console.error("❌ Failed to load:", err);
    policyContainer.innerHTML = "<p>❌ Error loading policies.</p>";
    lawContainer.innerHTML = "<p>❌ Error loading laws.</p>";
    summaryContainer.innerHTML = "<p>❌ Error loading summary.</p>";
  }
}

// ✅ Law Update Logic
async function updateLawToggles(headers) {
  const toggles = document.querySelectorAll(".law-toggle");
  const selected = Array.from(toggles)
    .filter(t => t.checked)
    .map(t => parseInt(t.dataset.id));

  try {
    const res = await fetch('/api/policies-laws/laws', {
      method: 'POST',
      headers,
      body: JSON.stringify({ law_ids: selected })
    });

    if (!res.ok) throw new Error('Failed');
    alert("✅ Laws updated!");
    await loadPoliciesAndLaws();
  } catch (err) {
    console.error("❌ Updating laws failed:", err);
    alert("Could not update laws.");
  }
}

// ✅ Summary Builder
function updateSummary(activePolicyId, activeLawsIds, policies, laws) {
  const container = document.getElementById("summary-content");
  container.innerHTML = "";

  const ul = document.createElement("ul");

  const policy = policies.find(p => p.id === activePolicyId);
  ul.innerHTML += `<li><strong>Policy:</strong> ${
    policy ? `${escapeHTML(policy.name)} — ${escapeHTML(policy.effect_summary)}` : "None selected"
  }</li>`;

  if (activeLawsIds.length === 0) {
    ul.innerHTML += "<li><strong>Laws:</strong> None selected.</li>";
  } else {
    activeLawsIds.forEach(id => {
      const law = laws.find(l => l.id === id);
      if (law) {
        ul.innerHTML += `<li><strong>Law:</strong> ${escapeHTML(law.name)} — ${escapeHTML(law.effect_summary)}</li>`;
      }
    });
  }

  container.appendChild(ul);
}

// ✅ HTML Escape
