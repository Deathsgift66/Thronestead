/*
Project Name: Kingmakers Rise Frontend
File Name: policies_laws.js
Date: June 2, 2025
Author: Deathsgift66
*/

import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  // ✅ authGuard.js already protects this page → no duplicate session check
  // ✅ Initial load
  await loadPoliciesAndLaws();
});

// ✅ Load Policies and Laws
async function loadPoliciesAndLaws() {
  const policyContainer = document.querySelector(".policy-options");
  const lawContainer = document.querySelector(".law-options");
  const summaryContainer = document.getElementById("summary-content");

  // Placeholders while loading
  policyContainer.innerHTML = "<p>Loading policies...</p>";
  lawContainer.innerHTML = "<p>Loading laws...</p>";
  summaryContainer.innerHTML = "<p>Building summary...</p>";

  try {
    // ✅ Load user profile
    const { data: { user } } = await supabase.auth.getUser();
    const { data: userData, error: userError } = await supabase
      .from('users')
      .select('active_policy, active_laws')
      .eq('user_id', user.id)
      .single();

    if (userError) throw userError;

    const activePolicy = userData.active_policy;
    const activeLaws = userData.active_laws || [];

    // ✅ Load catalog
    const { data: catalogData, error: catalogError } = await supabase
      .from('policies_laws_catalogue')
      .select('*');

    if (catalogError) throw catalogError;

    // Separate policies and laws
    const policies = catalogData.filter(item => item.type === "policy");
    const laws = catalogData.filter(item => item.type === "law");

    // ✅ Render Policies
    policyContainer.innerHTML = "";
    policies.forEach(policy => {
      const card = document.createElement("div");
      card.classList.add("policy-law-card");

      card.innerHTML = `
        <h3>${escapeHTML(policy.name)}</h3>
        <p>${escapeHTML(policy.description)}</p>
        <p>Effect: ${escapeHTML(policy.effect_summary)}</p>
        <button class="action-btn policy-select-btn" data-id="${policy.id}">Select Policy</button>
      `;

      // Highlight active
      if (policy.id === activePolicy) {
        card.classList.add("active-policy");
      }

      policyContainer.appendChild(card);
    });

    // ✅ Render Laws
    lawContainer.innerHTML = "";
    laws.forEach(law => {
      const card = document.createElement("div");
      card.classList.add("policy-law-card");

      const isActive = activeLaws.includes(law.id);

      card.innerHTML = `
        <h3>${escapeHTML(law.name)}</h3>
        <p>${escapeHTML(law.description)}</p>
        <p>Effect: ${escapeHTML(law.effect_summary)}</p>
        <label>
          <input type="checkbox" class="law-toggle" data-id="${law.id}" ${isActive ? "checked" : ""}>
          Active
        </label>
      `;

      lawContainer.appendChild(card);
    });

    // ✅ Bind policy select buttons
    document.querySelectorAll(".policy-select-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const policyId = btn.dataset.id;

        try {
          const { error } = await supabase
            .from('users')
            .update({ active_policy: policyId })
            .eq('user_id', user.id);

          if (error) throw error;

          alert("Policy updated!");
          await loadPoliciesAndLaws(); // Refresh
        } catch (err) {
          console.error("❌ Error updating policy:", err);
          alert("Failed to update policy.");
        }
      });
    });

    // ✅ Bind law toggles
    document.querySelectorAll(".law-toggle").forEach(toggle => {
      toggle.addEventListener("change", async () => {
        const lawId = parseInt(toggle.dataset.id);
        let updatedLaws = [...activeLaws];

        if (toggle.checked) {
          if (!updatedLaws.includes(lawId)) updatedLaws.push(lawId);
        } else {
          updatedLaws = updatedLaws.filter(id => id !== lawId);
        }

        try {
          const { error } = await supabase
            .from('users')
            .update({ active_laws: updatedLaws })
            .eq('user_id', user.id);

          if (error) throw error;

          alert("Laws updated!");
          await loadPoliciesAndLaws(); // Refresh
        } catch (err) {
          console.error("❌ Error updating laws:", err);
          alert("Failed to update laws.");
        }
      });
    });

    // ✅ Update summary
    updateSummary(activePolicy, activeLaws, policies, laws);

  } catch (err) {
    console.error("❌ Error loading policies/laws:", err);
    policyContainer.innerHTML = "<p>Failed to load policies.</p>";
    lawContainer.innerHTML = "<p>Failed to load laws.</p>";
    summaryContainer.innerHTML = "<p>Failed to build summary.</p>";
  }
}

// ✅ Update Summary Panel
function updateSummary(activePolicyId, activeLawsIds, policies, laws) {
  const summaryContainer = document.getElementById("summary-content");

  summaryContainer.innerHTML = "";

  const summaryList = document.createElement("ul");

  // Active policy
  const activePolicy = policies.find(p => p.id === activePolicyId);
  if (activePolicy) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>Policy:</strong> ${escapeHTML(activePolicy.name)} — ${escapeHTML(activePolicy.effect_summary)}`;
    summaryList.appendChild(li);
  } else {
    const li = document.createElement("li");
    li.innerHTML = "<strong>Policy:</strong> None selected.";
    summaryList.appendChild(li);
  }

  // Active laws
  if (activeLawsIds.length > 0) {
    activeLawsIds.forEach(id => {
      const law = laws.find(l => l.id === id);
      if (law) {
        const li = document.createElement("li");
        li.innerHTML = `<strong>Law:</strong> ${escapeHTML(law.name)} — ${escapeHTML(law.effect_summary)}`;
        summaryList.appendChild(li);
      }
    });
  } else {
    const li = document.createElement("li");
    li.innerHTML = "<strong>Laws:</strong> None selected.";
    summaryList.appendChild(li);
  }

  summaryContainer.appendChild(summaryList);
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
