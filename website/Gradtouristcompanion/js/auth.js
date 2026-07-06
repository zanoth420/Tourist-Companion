/* Shared auth helpers: session check, header rendering, logout. */

async function getMe() {
  try {
    const res = await fetch('/api/auth/me');
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

async function logout() {
  await fetch('/api/auth/logout', { method: 'POST' });
  window.location.href = 'index.html';
}

/* Renders the right side of the app header depending on login state.
   Pass the id of the <nav> element. */
let _lastNavId = null;

async function renderAuthNav(navId) {
  _lastNavId = navId;
  const nav = document.getElementById(navId);
  const me = await getMe();
  const T = k => (typeof t === 'function' ? t(k) : k);
  const base = `<a href="index.html">${T('nav.home')}</a>`
    + `<a href="programs.html">${T('nav.programs')}</a>`
    + `<a href="build.html">${T('nav.build')}</a>`;
  const toggles = (typeof langToggleHtml === 'function' ? langToggleHtml() : '')
    + (typeof themeToggleHtml === 'function' ? themeToggleHtml() : '');
  if (me) {
    nav.innerHTML = base
      + `<a href="mytrips.html">${T('nav.mytrips')}</a>`
      + (me.is_admin ? `<a href="admin.html">${T('nav.admin')}</a>` : '')
      + `<span class="user">${escapeHtml(me.name)}</span>`
      + `<a href="#" onclick="logout();return false;">${T('nav.logout')}</a>` + toggles;
  } else {
    nav.innerHTML = base + `<a href="Login.html">${T('nav.login')}</a>` + toggles;
  }
  if (typeof updateThemeIcons === 'function') updateThemeIcons();
  if (typeof updateLangToggles === 'function') updateLangToggles();
  return me;
}

// keep the nav in sync when the language switches
document.addEventListener('langchange', () => { if (_lastNavId) renderAuthNav(_lastNavId); });

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}
