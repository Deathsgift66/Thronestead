// Fetch diplomacy metrics
fetch('/api/diplomacy/summary')
  .then(res => res.json())
  .then(data => {
    document.getElementById('diplomacy-score').textContent = data.diplomacy_score;
    document.getElementById('active-treaties-count').textContent = data.active_treaties;
    document.getElementById('ongoing-wars-count').textContent = data.ongoing_wars;
  });

// Populate treaties
fetch('/api/diplomacy/treaties')
  .then(res => res.json())
  .then(data => {
    const tbody = document.getElementById('treaty-rows');
    data.forEach(treaty => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${treaty.treaty_type}</td>
        <td>${treaty.partner_name}</td>
        <td>${treaty.status}</td>
        <td>${new Date(treaty.signed_at).toLocaleDateString()}</td>
        <td>
          ${treaty.status === 'proposed' ? `
            <button onclick="respondTreaty(${treaty.treaty_id}, 'accept')">Accept</button>
            <button onclick="respondTreaty(${treaty.treaty_id}, 'reject')">Reject</button>
          ` : ''}
        </td>
      `;
      tbody.appendChild(row);
    });
  });

function proposeTreaty() {
  const type = document.getElementById('treaty-type').value;
  const partnerId = document.getElementById('partner-alliance-id').value;
  fetch('/api/diplomacy/propose_treaty', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ treaty_type: type, partner_alliance_id: partnerId })
  }).then(() => location.reload());
}

function respondTreaty(treatyId, action) {
  fetch('/api/diplomacy/respond_treaty', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ treaty_id: treatyId, response_action: action })
  }).then(() => location.reload());
}
