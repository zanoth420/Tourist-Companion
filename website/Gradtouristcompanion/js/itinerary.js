/* Shared itinerary module: plan rendering, Google Maps links, currency
   display, and .ics calendar export. Used by build.html, mytrips.html
   and share.html so the day-by-day markup exists in exactly one place. */

/* --- currency ------------------------------------------------------------ */

const Currency = {
  code: localStorage.getItem('tc_currency') || 'EGP',
  rates: null,   // {USD, EUR, GBP} per 1 EGP
  stale: false,
  symbols: { USD: '$', EUR: '€', GBP: '£' },

  async init(selectEl) {
    try {
      const data = await (await fetch('/api/rates')).json();
      this.rates = data.rates;
      this.stale = data.stale;
    } catch { /* stays EGP-only */ }
    if (selectEl) {
      selectEl.value = this.code;
      selectEl.addEventListener('change', () => {
        this.code = selectEl.value;
        localStorage.setItem('tc_currency', this.code);
        document.dispatchEvent(new Event('currencychange'));
      });
    }
  },

  fmt(egp) {
    if (egp === 0) return (typeof t === 'function' ? t('currency.free') : 'Free');
    if (this.code === 'EGP' || !this.rates || !this.rates[this.code]) {
      return `${egp} EGP`;
    }
    const v = egp * this.rates[this.code];
    const approx = this.stale ? '~' : '';
    return `${approx}${this.symbols[this.code]}${v.toFixed(v < 20 ? 2 : 0)}`;
  },
};

/* --- Google Maps links (no API key: Maps URLs) ---------------------------- */

function cleanPlaceName(name) {
  return name.replace(/\s*\([^)]*\)\s*$/, '');
}

function mapsPlaceUrl(stop) {
  const q = `${cleanPlaceName(stop.name)}, ${stop.area}, ${stop.city}, Egypt`;
  return 'https://www.google.com/maps/search/?api=1&query=' +
    encodeURIComponent(q) + '&utm_source=tourist_companion&utm_campaign=place_details_search';
}

function mapsDayRouteUrl(day) {
  const stops = day.stops;
  if (stops.length < 2) return stops.length ? mapsPlaceUrl(stops[0]) : null;
  const q = s => encodeURIComponent(`${cleanPlaceName(s.name)}, ${s.city}, Egypt`);
  let url = 'https://www.google.com/maps/dir/?api=1' +
    `&origin=${q(stops[0])}&destination=${q(stops[stops.length - 1])}`;
  const mid = stops.slice(1, -1).slice(0, 9);  // Maps URLs allow max 9 waypoints
  if (mid.length) url += '&waypoints=' + mid.map(q).join('%7C');
  return url + '&travelmode=driving&utm_source=tourist_companion&utm_campaign=directions_request';
}

/* --- rendering -------------------------------------------------------------- */

const _esc = s => { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; };

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function prettyDate(iso) {
  const d = new Date(iso + 'T00:00:00');
  return `${DAY_NAMES[d.getDay()]}, ${MONTHS[d.getMonth()]} ${d.getDate()}`;
}

/* Renders the day cards into `container`.
   opts.interactive = {lockedIds:Set, onRemove(id), onToggleLock(id)} enables
   the per-stop lock/remove buttons (build page only). */
function renderItinerary(container, plan, opts = {}) {
  const it = opts.interactive;
  const ar = typeof getLang === 'function' && getLang() === 'ar';
  const cityLabel = c => (typeof tCity === 'function' ? tCity(c) : c);
  let html = '';
  for (const day of plan.days) {
    const dateLabel = day.date ? ` · ${prettyDate(day.date)}` : '';
    const route = mapsDayRouteUrl(day);
    const routeLink = route
      ? ` <a class="day-link" href="${route}" target="_blank" rel="noopener">${t('itin.route')}</a>` : '';
    const stops = day.stops.map(s => {
      let actions = '';
      if (it) {
        const locked = it.lockedIds.has(s.id);
        actions = `
          <span class="stop-actions">
            <button class="icon-btn ${locked ? 'on' : ''}" title="${locked ? 'Unlock' : 'Lock as must-see'}"
              onclick="${it.ns}.toggleLock('${s.id}')">${locked ? '🔒' : '🔓'}</button>
            <button class="icon-btn" title="Remove and re-plan"
              onclick="${it.ns}.removeStop('${s.id}')">✕</button>
          </span>`;
      }
      return `
        <div class="stop">
          <span class="time">${s.arrive}–${s.depart}</span>
          <span class="name">${_esc(ar && s.name_ar ? s.name_ar : s.name)}${s.needs_verification ? ' *' : ''}
            <a class="map-link" href="${mapsPlaceUrl(s)}" target="_blank"
               rel="noopener" title="Open in Google Maps">📍</a>
            <span class="meta"> ${_esc(ar && s.area_ar ? s.area_ar : s.area)} · ★${s.rating}</span>
            ${s.after_hours ? `<span class="warn"> ${t('itin.after_hours')}</span>` : ''}
          </span>
          ${actions}
          <span class="price" data-egp="${s.price}">${Currency.fmt(s.price)}</span>
        </div>`;
    }).join('');
    html += `
      <div class="day">
        <div class="day-head">
          <span>${t('itin.day')} ${day.day} — ${_esc(cityLabel(day.city))}${dateLabel}</span>
          <span><span data-egp="${day.total_cost}">${Currency.fmt(day.total_cost)}</span>
            · ${t('itin.done_by')} ${day.end}${routeLink}</span>
        </div>
        ${stops}
      </div>`;
  }
  if (plan.unscheduled && plan.unscheduled.length) {
    html += `<p class="warn">${t('itin.couldnt_fit')} ${plan.unscheduled.map(_esc).join(', ')} —
      ${t('itin.try_more')}</p>`;
  }
  container.innerHTML = html;
}

/* Re-formats every rendered price in place when the currency changes. */
document.addEventListener('currencychange', () => {
  document.querySelectorAll('[data-egp]').forEach(el => {
    el.textContent = Currency.fmt(+el.dataset.egp);
  });
});

/* --- .ics calendar export ------------------------------------------------------ */

function _icsEscape(s) {
  return s.replace(/\\/g, '\\\\').replace(/[,;]/g, m => '\\' + m);
}

function icsForPlan(plan, tripName) {
  const today = new Date();
  const fallbackStart = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const stamp = today.toISOString().replace(/[-:]/g, '').replace(/\.\d+/, '');
  const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0',
                 'PRODID:-//Tourist Companion//EN', 'CALSCALE:GREGORIAN'];
  for (const day of plan.days) {
    let ymd;
    if (day.date) {
      ymd = day.date.replace(/-/g, '');
    } else {
      const d = new Date(fallbackStart);
      d.setDate(d.getDate() + day.day - 1);
      ymd = d.toISOString().slice(0, 10).replace(/-/g, '');
    }
    for (const s of day.stops) {
      lines.push(
        'BEGIN:VEVENT',
        `UID:${ymd}-${s.id}@tourist-companion`,
        `DTSTAMP:${stamp}`,
        `DTSTART:${ymd}T${s.arrive.replace(':', '')}00`,
        `DTEND:${ymd}T${s.depart.replace(':', '')}00`,
        `SUMMARY:${_icsEscape(s.name)}`,
        `LOCATION:${_icsEscape(`${s.area}, ${s.city}, Egypt`)}`,
        `DESCRIPTION:${_icsEscape(`Ticket: ${s.price} EGP. Part of "${tripName}" — Tourist Companion.`)}`,
        'END:VEVENT');
    }
  }
  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

function downloadIcs(plan, tripName) {
  const blob = new Blob([icsForPlan(plan, tripName)], { type: 'text/calendar' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  // \p{L}\p{N} keeps non-Latin (e.g. Arabic) trip names readable in the filename
  a.download = tripName.replace(/[^\p{L}\p{N}-]+/gu, '_').toLowerCase() + '.ics';
  a.click();
  URL.revokeObjectURL(a.href);
}
