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
async function renderAuthNav(navId) {
  const nav = document.getElementById(navId);
  const me = await getMe();
  const base = '<a href="index.html">Home</a><a href="build.html">Build Trip</a>';
  if (me) {
    nav.innerHTML = base
      + '<a href="mytrips.html">My Trips</a>'
      + `<span class="user">${escapeHtml(me.name)}</span>`
      + '<a href="#" onclick="logout();return false;">Logout</a>';
  } else {
    nav.innerHTML = base + '<a href="Login.html">Login</a>';
  }
  return me;
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}
