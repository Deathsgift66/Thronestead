// Project Name: Thronestead©
// File Name: legal.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
document.addEventListener('DOMContentLoaded', () => {
  const legalDocs = [
    {
      title: 'Privacy Policy',
      file: '/Assets/legal/THRONESTEAD_PrivacyPolicy.pdf',
      desc: 'How we collect, use, and protect your data.'
    },
    {
      title: 'Terms of Service',
      file: '/Assets/legal/THRONESTEAD_TermsofService.pdf',
      desc: 'Your rights and responsibilities as a player.'
    },
    {
      title: 'End User License Agreement (EULA)',
      file: '/Assets/legal/THRONESTEAD_EULA.pdf',
      desc: 'Game usage terms and content licensing.'
    },
    {
      title: 'Cookie Policy',
      file: '/Assets/legal/THRONESTEAD_CookiePolicy.pdf',
      desc: 'Our use of browser cookies and tracking.'
    },
    {
      title: 'Community Guidelines',
      file: '/Assets/legal/THRONESTEAD_GameRules.pdf',
      desc: 'Code of conduct for players and alliance members.'
    },
    {
      title: 'Data Processing Addendum (DPA)',
      file: '/Assets/legal/THRONESTEAD_DPA.pdf',
      desc: 'GDPR-compliant processing terms.'
    }
  ];

  const docGrid = document.getElementById('legal-docs');
  const searchInput = document.getElementById('doc-search');

  function renderDocs(filter = '') {
    docGrid.innerHTML = '';
    const filtered = legalDocs.filter(doc =>
      doc.title.toLowerCase().includes(filter.toLowerCase()) ||
      doc.desc.toLowerCase().includes(filter.toLowerCase())
    );

    if (filtered.length === 0) {
      docGrid.innerHTML = '<p>No documents found.</p>';
      return;
    }

    filtered.forEach(doc => {
      const card = document.createElement('div');
      card.className = 'legal-card';
      card.innerHTML = `
        <h3>${doc.title}</h3>
        <p>${doc.desc}</p>
        <a class="btn" href="${doc.file}" target="_blank" rel="noopener">📄 View PDF</a>
      `;
      docGrid.appendChild(card);
    });
  }

  searchInput.addEventListener('input', () => {
    renderDocs(searchInput.value);
  });

  renderDocs();
});
