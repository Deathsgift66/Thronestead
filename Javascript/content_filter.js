// Codex script: strict name/content filtering using banned_words.json
// This module loads banned words and flags or blocks any user input that matches or embeds them

import bannedWords from '../banned_words.json';

// Normalize and flatten banned word list for quick lookup
const bannedSet = new Set(bannedWords.map(word => word.toLowerCase()));

// Utility: Normalize user input (remove punctuation, lowercased, etc.)
function normalizeInput(str) {
  return str
    .toLowerCase()
    .replace(/[\s\-_]/g, '')
    .replace(/[^a-z0-9]/gi, '');
}

// Check input against banned words (exact match or embedded match)
function containsBannedContent(input) {
  const normalized = normalizeInput(input);
  for (const banned of bannedSet) {
    if (normalized.includes(banned)) {
      return true;
    }
  }
  return false;
}

// Display confirmation modal
function showFlaggedWarning(onConfirm, onCancel) {
  const modal = document.createElement('div');
  modal.id = 'banned-word-warning';
  modal.innerHTML = `
    <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:#000a;display:flex;justify-content:center;align-items:center;z-index:9999">
      <div style="background:#fff;padding:20px;border-radius:8px;width:400px;max-width:90%">
        <h3>⚠️ Content Warning</h3>
        <p>Your input contains potentially banned words. This content will be flagged for admin review.</p>
        <p>If found inappropriate, disciplinary actions may be taken, including temporary or permanent bans.</p>
        <div style="display:flex;justify-content:space-between;margin-top:20px">
          <button id="confirm-banned" style="background:#e00;color:#fff;padding:8px 16px;border:none;border-radius:4px">Proceed Anyway</button>
          <button id="cancel-banned" style="background:#888;color:#fff;padding:8px 16px;border:none;border-radius:4px">Cancel</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  document.getElementById('confirm-banned').onclick = () => {
    modal.remove();
    onConfirm();
  };
  document.getElementById('cancel-banned').onclick = () => {
    modal.remove();
    onCancel();
  };
}

// Main hook for input validation
export function validateInputField(inputElement, logToAdminReview) {
  inputElement.addEventListener('change', () => {
    const value = inputElement.value;
    if (containsBannedContent(value)) {
      showFlaggedWarning(
        () => {
          // User confirmed — flag for admin
          logToAdminReview({
            input: value,
            timestamp: new Date().toISOString(),
            field: inputElement.name || inputElement.id || 'unknown',
            status: 'Flagged for Review'
          });
        },
        () => {
          // User canceled — clear field
          inputElement.value = '';
        }
      );
    }
  });
}

// Example logger (you'd replace this with an API call)
export function logToAdminReview(entry) {
  console.log('[ADMIN LOG]', entry);
  // You can replace with:
  // fetch('/api/moderation/flagged', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify(entry)
  // });
}
