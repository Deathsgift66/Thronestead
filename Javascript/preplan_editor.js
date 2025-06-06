/* Pre-plan editor basic interactions */

document.addEventListener('DOMContentLoaded', () => {
  const createBtn = document.getElementById('save-plan');
  if (!createBtn) return;

  createBtn.addEventListener('click', async () => {
    const warId = document.getElementById('war-id').value;
    const payload = { orders: [] };
    await fetch(`/api/start-battle/${warId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    alert('Pre-plan saved and battle started');
  });
});
