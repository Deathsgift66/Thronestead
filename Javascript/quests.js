document.getElementById("js-disabled-message")?.remove();
// Project Name: Thronestead©
// File Name: quests.js 
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
import { supabase } from '/Javascript/supabaseClient.js';
import {
  escapeHTML,
  showToast,
  openModal,
  closeModal,
  authFetch
} from './utils.js';

let questChannel = null;
let cachedKingdomId = null;
let pendingQuest = null;

document.addEventListener('DOMContentLoaded', async () => {
  await loadKingdomQuests();

  if (cachedKingdomId) {
questChannel = supabase
  .channel('public:quest_kingdom_tracking')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'quest_kingdom_tracking',
      filter: `kingdom_id=eq.${cachedKingdomId}`
    },
    async () => {
      await loadKingdomQuests();
    }
  )
  .subscribe();

window.addEventListener('beforeunload', () => {
  if (questChannel) supabase.removeChannel(questChannel);
});
  }

  document.getElementById('accept-yes')?.addEventListener('click', () => {
if (!pendingQuest) return;
acceptQuest(pendingQuest.code, pendingQuest.btn);
pendingQuest = null;
closeModal('accept-modal');
  });
  document.getElementById('accept-no')?.addEventListener('click', () => {
pendingQuest = null;
closeModal('accept-modal');
  });
});

async function loadKingdomQuests() {
  const catalogueEl = document.getElementById('quest-catalogue');
  const activeEl = document.getElementById('active-quests');
  const completedEl = document.getElementById('completed-quests');

  catalogueEl.innerHTML = '<p>Loading quests...</p>';
  activeEl.innerHTML = '<p>Loading active quests...</p>';
  completedEl.innerHTML = '<p>Loading completed quests...</p>';

  try {
const {
  data: { user }
} = await supabase.auth.getUser();
if (!cachedKingdomId) {
  const { data: userData, error: userError } = await supabase
    .from('users')
    .select('kingdom_id')
    .eq('user_id', user.id)
    .single();
  if (userError) throw userError;
  cachedKingdomId = userData.kingdom_id;
}

const kingdomId = cachedKingdomId;
const castleLevel = window.playerProgression?.castleLevel || 1;

const [catalogue, tracking] = await Promise.all([
  supabase
    .from('quest_kingdom_catalogue')
    .select('*')
    .eq('is_active', true)
    .lte('required_level', castleLevel),
  supabase
    .from('quest_kingdom_tracking')
    .select('*')
    .eq('kingdom_id', kingdomId)
]);

if (catalogue.error || tracking.error)
  throw new Error('Failed to load quests');

const catalogueData = catalogue.data || [];
const trackingData = tracking.data || [];

renderQuestCatalogue(catalogueData, trackingData);
renderActiveQuests(
  trackingData.filter(q => q.status === 'active'),
  catalogueData
);
renderCompletedQuests(
  trackingData.filter(q => q.status === 'completed'),
  catalogueData
);

startCountdownTimers();
  } catch (err) {
console.error('❌ Failed to load quests:', err);
catalogueEl.innerHTML = '<p>Failed to load quest catalogue.</p>';
activeEl.innerHTML = '<p>Failed to load active quests.</p>';
completedEl.innerHTML = '<p>Failed to load completed quests.</p>';
  }
}

function renderQuestCatalogue(catalogue, tracking) {
  const container = document.getElementById('quest-catalogue');
  container.innerHTML = '';

  const activeCodes = new Set(
tracking.filter(q => q.status === 'active').map(q => q.quest_code)
  );
  const completedCodes = new Set(
tracking.filter(q => q.status === 'completed').map(q => q.quest_code)
  );

  for (const quest of catalogue) {
const isActive = activeCodes.has(quest.quest_code);
const isCompleted = completedCodes.has(quest.quest_code);
const card = document.createElement('div');
card.className = 'quest-card';

card.innerHTML = `
  <h3>${escapeHTML(quest.name)}</h3>
  <p>${escapeHTML(quest.description)}</p>
  <p>Category: ${escapeHTML(quest.category || '')}</p>
  <p><strong>Objectives:</strong></p><ul>${formatJsonList(
quest.objectives
  )}</ul>
  <p><strong>Rewards:</strong></p><ul>${formatJsonList(
quest.rewards
  )}</ul>
  <p>Duration: ${quest.duration_hours}h</p>
  <p>${quest.repeatable ? `Repeatable${quest.max_attempts ? ` (Max ${quest.max_attempts})` : ''}` : 'One-time'}</p>
  <button class="action-btn accept-quest-btn" data-code="${quest.quest_code}" ${isActive || (!quest.repeatable && isCompleted) ? 'disabled' : ''}>
${isActive ? 'Already Active' : isCompleted && !quest.repeatable ? 'Completed' : 'Accept Quest'}
  </button>
`;
container.appendChild(card);
  }

  document.querySelectorAll('.accept-quest-btn').forEach(btn => {
btn.addEventListener('click', () => {
  const questCode = btn.dataset.code;
  pendingQuest = { code: questCode, btn };
  document.getElementById('accept-body').textContent = `Accept quest "${questCode}"?`;
  openModal('accept-modal');
});
  });
}

function renderActiveQuests(list, catalogue) {
  const container = document.getElementById('active-quests');
  container.innerHTML = '';

  if (!list.length) {
container.innerHTML = '<p>No active quests.</p>';
return;
  }

  for (const quest of list) {
const def = catalogue.find(c => c.quest_code === quest.quest_code);
const endMs = Date.parse(quest.ends_at);
const remaining = Number.isFinite(endMs)
  ? Math.max(0, Math.floor((endMs - Date.now()) / 1000))
  : 0;
const card = document.createElement('div');
card.className = 'quest-card';
card.innerHTML = `
  <h3>${escapeHTML(def?.name || quest.quest_code)}</h3>
  <p>${escapeHTML(def?.description || '')}</p>
  <p>Time Remaining: <span class="countdown" data-ends-at="${quest.ends_at}">${
Number.isFinite(endMs) ? formatTime(remaining) : 'Unknown'
  }</span></p>
  <p>Progress: ${quest.progress}%</p>
`;
container.appendChild(card);
  }
}

function renderCompletedQuests(list, catalogue) {
  const container = document.getElementById('completed-quests');
  container.innerHTML = '';

  if (!list.length) {
container.innerHTML = '<p>No completed quests.</p>';
return;
  }

  for (const quest of list) {
const def = catalogue.find(c => c.quest_code === quest.quest_code);
const card = document.createElement('div');
card.className = 'quest-card';
card.innerHTML = `
  <h3>${escapeHTML(def?.name || quest.quest_code)}</h3>
  <p>${escapeHTML(def?.description || '')}</p>
  <p>Completed on: ${(() => {
const d = new Date(quest.ends_at);
return isNaN(d) ? 'Unknown' : d.toLocaleString();
  })()}</p>
`;
container.appendChild(card);
  }
}

function startCountdownTimers() {
  const elements = document.querySelectorAll('.countdown');
  elements.forEach(el => {
const endsAt = Date.parse(el.dataset.endsAt);
if (!Number.isFinite(endsAt)) {
  el.textContent = 'Invalid date';
  return;
}
const update = () => {
  const seconds = Math.max(0, Math.floor((endsAt - Date.now()) / 1000));
  el.textContent = formatTime(seconds);
  if (seconds <= 0) {
    clearInterval(interval);
    el.textContent = 'Completed!';
  }
};
update();
const interval = setInterval(update, 1000);
  });
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

function formatJsonList(json) {
  try {
const obj = typeof json === 'string' ? JSON.parse(json) : json;
return Object.entries(obj)
  .map(([k, v]) =>
    `<li>${escapeHTML(k)}: ${
      typeof v === 'object' ? JSON.stringify(v) : escapeHTML(String(v))
    }</li>`
  )
  .join('');
  } catch {
return `<li>${escapeHTML(String(json))}</li>`;
  }
}

function showInlineError(btn, msg) {
  let span = btn.nextElementSibling;
  if (!span || !span.classList.contains('error-inline')) {
span = document.createElement('span');
span.className = 'error-inline';
btn.insertAdjacentElement('afterend', span);
  }
  span.textContent = msg;
  setTimeout(() => span.remove(), 3000);
}

function acceptQuest(code, btn) {
  btn.disabled = true;
  authFetch('/api/kingdom/accept_quest', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ quest_code: code })
  })
.then(res => {
  if (!res.ok) throw new Error('Request failed');
  showToast('Quest accepted!');
  return loadKingdomQuests();
})
.catch(err => {
  console.error('❌ Accept failed:', err);
  showToast('Failed to accept quest');
  showInlineError(btn, 'Failed to accept');
})
.finally(() => {
  btn.disabled = false;
});
}

