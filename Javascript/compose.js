import { supabase } from '../supabaseClient.js';
import { authFetchJson } from './fetchJson.js';
import { showToast, getValue, setText } from './utils.js';

let session;

document.addEventListener('DOMContentLoaded', async () => {
  const { data: { session: s } } = await supabase.auth.getSession();
  if (!s) {
    window.location.href = 'login.html';
    return;
  }
  session = s;
  setupTabs();
  setupForms();
});

function setupTabs() {
  const tabs = document.querySelectorAll('.tab');
  const contents = document.querySelectorAll('.tab-content');
  tabs.forEach(t => {
    t.addEventListener('click', () => {
      tabs.forEach(b => b.classList.remove('active'));
      contents.forEach(c => c.classList.remove('active'));
      t.classList.add('active');
      document.getElementById(t.dataset.tab).classList.add('active');
    });
  });
}

function setupForms() {
  const msgForm = document.getElementById('message-form');
  const noticeForm = document.getElementById('notice-form');
  const treatyForm = document.getElementById('treaty-form');
  const warForm = document.getElementById('war-form');

  if (msgForm) {
    const preview = document.getElementById('msg-preview');
    msgForm.addEventListener('input', () => {
      setText('msg-preview', getValue('msg-content'));
    });
    msgForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await authFetchJson('/api/compose/message', session, {
          method: 'POST',
          body: JSON.stringify({
            recipient_id: getValue('msg-recipient'),
            message: getValue('msg-content')
          })
        });
        showToast('Message sent');
        msgForm.reset();
        preview.textContent = '';
      } catch (err) {
        showToast(err.message);
      }
    });
  }

  if (noticeForm) {
    noticeForm.addEventListener('input', () => {
      setText('notice-preview', getValue('notice-message'));
    });
    noticeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await authFetchJson('/api/compose/notice', session, {
          method: 'POST',
          body: JSON.stringify({
            title: getValue('notice-title'),
            message: getValue('notice-message'),
            category: getValue('notice-category', true),
            link_action: getValue('notice-link', true),
            image_url: getValue('notice-image-url', true),
            expires_at: getValue('notice-expires', true)
          })
        });
        showToast('Notice created');
        noticeForm.reset();
        setText('notice-preview', '');
      } catch (err) {
        showToast(err.message);
      }
    });
  }

  if (treatyForm) {
    treatyForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await authFetchJson('/api/compose/treaty', session, {
          method: 'POST',
          body: JSON.stringify({
            partner_alliance_id: parseInt(getValue('treaty-partner')), 
            treaty_type: getValue('treaty-type')
          })
        });
        showToast('Treaty proposed');
        treatyForm.reset();
      } catch (err) {
        showToast(err.message);
      }
    });
  }

  if (warForm) {
    warForm.addEventListener('input', () => {
      setText('war-preview', getValue('war-reason'));
    });
    warForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await authFetchJson('/api/compose/war', session, {
          method: 'POST',
          body: JSON.stringify({
            defender_id: getValue('war-defender'),
            war_reason: getValue('war-reason')
          })
        });
        showToast('War declared');
        warForm.reset();
        setText('war-preview', '');
      } catch (err) {
        showToast(err.message);
      }
    });
  }
}
