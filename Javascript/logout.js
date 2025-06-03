async function logout() {
  try {
    await supabase.auth.signOut(); // End Supabase session
  } catch (err) {
    console.warn('Supabase logout error:', err.message);
  }

  sessionStorage.removeItem('authToken');
  localStorage.removeItem('authToken');
  document.cookie = "authToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=" + window.location.hostname;

  window.location.href = 'login.html';
}

const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) logoutBtn.addEventListener('click', logout);
