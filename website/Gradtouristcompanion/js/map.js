/* Interactive trip map: numbered markers + per-day route lines on a Google Map.
   The browser API key is served by GET /api/config (referrer-restricted). With
   no key configured the map container simply hides, so the whole itinerary keeps
   working without any Google dependency. Used by build.html, mytrips.html and
   share.html — call TripMap.render(container, plan) after renderItinerary(). */

const TripMap = {
  _keyPromise: null,
  _sdkPromise: null,
  // one colour per day (wraps around for long trips)
  _colors: ['#c9a24b', '#3f7cac', '#c1573f', '#4c9a6a', '#8e5aa8', '#c98a2b', '#5b8db8'],

  _key() {
    if (!this._keyPromise) {
      this._keyPromise = fetch('/api/config')
        .then(r => r.json()).then(c => c.maps_key || '').catch(() => '');
    }
    return this._keyPromise;
  },

  _loadSdk(key) {
    if (this._sdkPromise) return this._sdkPromise;
    this._sdkPromise = new Promise((resolve, reject) => {
      if (window.google && window.google.maps) return resolve();
      const s = document.createElement('script');
      s.src = 'https://maps.googleapis.com/maps/api/js?v=weekly&key=' + encodeURIComponent(key);
      s.async = true;
      s.onload = resolve;
      s.onerror = () => reject(new Error('Google Maps failed to load'));
      document.head.appendChild(s);
    });
    return this._sdkPromise;
  },

  async render(container, plan) {
    if (!container) return;
    container.style.display = 'none';            // hidden until we know we can draw
    const key = await this._key();
    if (!key) return;

    const days = plan.days || [];
    const hasCoords = days.some(d => d.stops.some(s => s.lat != null && s.lon != null));
    if (!hasCoords) return;

    try { await this._loadSdk(key); } catch { return; }

    container.style.display = '';
    const map = new google.maps.Map(container, {
      mapTypeControl: false, streetViewControl: false, fullscreenControl: true,
    });
    const bounds = new google.maps.LatLngBounds();
    const info = new google.maps.InfoWindow();
    const esc = t => String(t).replace(/[&<>"]/g,
      c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

    days.forEach((day, di) => {
      const color = this._colors[di % this._colors.length];
      const path = [];
      day.stops.forEach((s, si) => {
        if (s.lat == null || s.lon == null) return;
        const pos = { lat: +s.lat, lng: +s.lon };
        path.push(pos);
        bounds.extend(pos);
        const marker = new google.maps.Marker({
          position: pos, map, title: s.name,
          label: { text: String(si + 1), color: '#fff', fontSize: '12px', fontWeight: '600' },
          icon: {
            path: google.maps.SymbolPath.CIRCLE, fillColor: color, fillOpacity: 1,
            strokeColor: '#fff', strokeWeight: 2, scale: 11,
          },
        });
        marker.addListener('click', () => {
          info.setContent(
            `<div style="font:600 13px sans-serif;color:#222">Day ${day.day} · stop ${si + 1}` +
            `<br><span style="font-weight:400">${esc(s.name)}</span></div>`);
          info.open(map, marker);
        });
      });
      if (path.length > 1) {
        new google.maps.Polyline({
          path, map, strokeColor: color, strokeOpacity: 0.85, strokeWeight: 3,
        });
      }
    });

    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, 48);
      google.maps.event.addListenerOnce(map, 'idle', () => {
        if (map.getZoom() > 15) map.setZoom(15);   // don't over-zoom a single point
      });
    }
  },
};

// `const` at top level doesn't attach to window; expose it so pages can guard
// on `window.TripMap` and skip cleanly if this script fails to load.
window.TripMap = TripMap;
