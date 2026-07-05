/* Theme: dark by default, light optional. Applied to <html> before paint
   (this file is loaded in <head>) so there's no flash on load. */

(function () {
  const stored = localStorage.getItem('tc_theme');
  document.documentElement.setAttribute('data-theme', stored || 'dark');
})();

function toggleTheme() {
  const next = document.documentElement.getAttribute('data-theme') === 'dark'
    ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('tc_theme', next);
  updateThemeIcons();
}

function updateThemeIcons() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.querySelectorAll('.theme-toggle').forEach(b => {
    b.textContent = dark ? '☀' : '☾';
    b.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
  });
}

function themeToggleHtml() {
  return '<button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">☀</button>';
}

/* Inject a mobile hamburger into every app header and wire it to toggle
   the nav (CSS shows .app-header.open nav on small screens). */
function initMobileNav() {
  document.querySelectorAll('header.app-header').forEach(h => {
    const nav = h.querySelector('nav');
    if (!nav || h.querySelector('.nav-icon')) return;
    const btn = document.createElement('button');
    btn.className = 'nav-icon';
    btn.textContent = '☰';
    btn.setAttribute('aria-label', 'Toggle menu');
    btn.onclick = () => h.classList.toggle('open');
    h.insertBefore(btn, nav);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  updateThemeIcons();
  initMobileNav();
});
