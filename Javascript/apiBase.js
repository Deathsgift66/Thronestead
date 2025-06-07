const API_BASE_URL = window.API_BASE_URL || 'https://kingmakers-backend.onrender.com';

// Global public pages — bypass auth check
const PUBLIC_PAGES = [
  '', // root path
  'index.html',
  'signup.html',
  'signin.html',
  'login.html',
  'legal.html',
  'PrivacyPolicy.html',
  'TermsofService.html',
  'EULA.html'
];

// Enforce authentication for all non-public pages
document.addEventListener('DOMContentLoaded', async () => {
  const currentPage = window.location.pathname.split('/').pop();

  if (!PUBLIC_PAGES.includes(currentPage)) {
    const { supabase } = await import('./supabaseClient.js');
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      console.warn(`Redirecting unauthenticated user from ${currentPage} to login.`);
      window.location.href = 'login.html';
    }
  }
});

const originalFetch = window.fetch;
window.fetch = (input, init) => {
  if (typeof input === 'string' && input.startsWith('/')) {
    input = API_BASE_URL + input;
  }
  return originalFetch(input, init);
};
