// Project Name: Thronestead©
// File Name: profile.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '../supabaseClient.js';
import { escapeHTML } from './utils.js';

document.addEventListener("DOMContentLoaded", async () => {
  await loadPlayerProfile();
});

// ✅ Main Profile Loader
async function loadPlayerProfile() {
  const avatarImg = document.getElementById("profile-picture");
  const playerNameEl = document.getElementById("player-name");
  const kingdomNameEl = document.getElementById("kingdom-name");
  const mottoEl = document.getElementById("player-motto");
  const vipBadgeEl = document.getElementById("vip-badge");
  const prestigeEl = document.getElementById("prestige-score");
  const titlesListEl = document.getElementById("titles-list");
  const customizationContainer = document.getElementById("profile-customization-content");
  const lastLoginEl = document.getElementById("last-login");
  const banWarningEl = document.getElementById("ban-warning");
  const recentActionsEl = document.querySelector('.recent-actions');

  playerNameEl.textContent = "Loading...";
  kingdomNameEl.textContent = "Loading...";
  mottoEl.textContent = "Loading...";
  customizationContainer.innerHTML = "<p>Loading customization options...</p>";

  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    const headers = {
      'Authorization': `Bearer ${session.access_token}`,
      'X-User-ID': session.user.id
    };

    // ✅ Load profile overview
    const profileRes = await fetch('/api/profile/overview', { headers });
    const overview = await profileRes.json();
    if (!profileRes.ok) throw new Error(overview.detail || 'Profile load failed');

    const data = overview.user || {};
    avatarImg.src = data.profile_avatar_url || "/Assets/avatars/default_avatar_emperor.png";
    avatarImg.alt = `${data.username || 'Player'}'s Avatar`;

    playerNameEl.textContent = data.username || "Unnamed Player";
    kingdomNameEl.textContent = data.kingdom_name || "Unnamed Kingdom";
    mottoEl.textContent = data.profile_bio || "No motto set.";
    if (lastLoginEl) {
      const ts = data.last_login_at ? new Date(data.last_login_at) : null;
      lastLoginEl.textContent = ts ? `Last Login: ${ts.toLocaleString()}` : '';
    }

    if (data.is_banned) {
      banWarningEl.classList.remove('hidden');
      vipBadgeEl.style.display = 'none';
      customizationContainer.innerHTML = '';
      if (recentActionsEl) recentActionsEl.classList.add('hidden');
    } else {
      banWarningEl.classList.add('hidden');
      if (recentActionsEl) recentActionsEl.classList.remove('hidden');
    }

    // ✅ VIP badge
    try {
      const vipRes = await fetch('/api/kingdom/vip_status', { headers });
      const vipData = await vipRes.json();
      const lvl = vipData.vip_level || 0;
      vipBadgeEl.textContent = lvl > 0 ? `VIP ${lvl}` : '';
      vipBadgeEl.style.display = lvl > 0 ? 'inline-block' : 'none';
    } catch {
      vipBadgeEl.style.display = 'none';
    }

    // ✅ Prestige + Titles
    try {
      const [prestigeRes, titlesRes] = await Promise.all([
        fetch('/api/kingdom/prestige', { headers }),
        fetch('/api/kingdom/titles', { headers })
      ]);
      const prestige = await prestigeRes.json();
      const titles = await titlesRes.json();

      prestigeEl.textContent = `Prestige: ${prestige.prestige_score ?? 0}`;
      titlesListEl.innerHTML = '';
      (titles.titles || []).forEach(title => {
        const li = document.createElement('li');
        const name = title.title ?? title; // fallback if API returns string
        if (title.awarded_at) {
          const date = formatTimestamp(title.awarded_at);
          li.textContent = `${name} — awarded ${date}`;
        } else {
          li.textContent = name;
        }
        titlesListEl.appendChild(li);
      });
    } catch {
      prestigeEl.textContent = 'Prestige: --';
      titlesListEl.innerHTML = '';
    }

    // ✅ Profile customization
    customizationContainer.innerHTML = `
      <h3>Customize Profile</h3>
      <button class="action-btn" id="edit-avatar-btn">Change Avatar</button>
      <button class="action-btn" id="edit-banner-btn">Change Banner</button>
      <button class="action-btn" id="edit-border-btn">Change Border</button>
      <button class="action-btn" id="edit-motto-btn">Edit Motto</button>
    `;
    customizationContainer.querySelectorAll(".action-btn").forEach(btn =>
      btn.addEventListener("click", () =>
        alert('🛠️ This customization feature is coming soon.')
      )
    );

    // ✅ Activity log + real-time updates
    await loadRecentActions(session.user.id);
    subscribeRecentActions(session.user.id);

  } catch (err) {
    console.error("❌ Error loading profile:", err);
    playerNameEl.textContent = "Failed to load.";
    kingdomNameEl.textContent = "Failed to load.";
    mottoEl.textContent = "Failed to load.";
    customizationContainer.innerHTML = "<p>Failed to load customization options.</p>";
  }
}

// ✅ Load Recent Activity Log
async function loadRecentActions(userId) {
  const tbody = document.getElementById('recent-log-body');
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="3">Loading...</td></tr>`;

  try {
    const res = await fetch(`/api/audit-log?user_id=${encodeURIComponent(userId)}&limit=10`);
    const data = await res.json();

    tbody.innerHTML = '';
    if (!data.logs?.length) {
      tbody.innerHTML = `<tr><td colspan="3">No recent activity.</td></tr>`;
      return;
    }

    data.logs.forEach(log => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${formatTimestamp(log.created_at)}</td>
        <td>${escapeHTML(log.action)}</td>
        <td>${escapeHTML(log.details)}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("❌ Error loading audit log:", err);
    tbody.innerHTML = `<tr><td colspan="3">Failed to load.</td></tr>`;
  }
}

// ✅ Subscribe to real-time audit log updates
let auditChannel = null;

function subscribeRecentActions(userId) {
  if (auditChannel) supabase.removeChannel(auditChannel);
  auditChannel = supabase
    .channel(`audit_log:user:${userId}`)
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'audit_log',
        filter: `user_id=eq.${userId}`
      },
      payload => addAuditEntry(payload.new)
    )
    .subscribe();
}

// ✅ Add new audit entry live
function addAuditEntry(entry) {
  const tbody = document.getElementById('recent-log-body');
  if (!tbody) return;
  const row = document.createElement('tr');
  row.innerHTML = `
    <td>${formatTimestamp(entry.created_at)}</td>
    <td>${escapeHTML(entry.action)}</td>
    <td>${escapeHTML(entry.details)}</td>
  `;
  tbody.prepend(row);
  if (tbody.rows.length > 10) tbody.deleteRow(-1); // Keep at 10 max
}

// ✅ Timestamp Formatter
function formatTimestamp(timestamp) {
  if (!timestamp) return 'Unknown';
  const date = new Date(timestamp);
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

