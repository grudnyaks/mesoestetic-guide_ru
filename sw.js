/* Офлайн-режим веб-версии.
   Сам справочник (index.html, version.json) — сначала из сети: открывается всегда свежая версия,
   а без интернета или при медленной сети (дольше 3,5 с) — из кэша.
   Иконки и прочее — из кэша мгновенно, с фоновым обновлением. */
const CACHE = 'meso-guide-v2';
const CORE = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
const fresh = req => /\/$|index\.html$|version\.json$/.test(new URL(req.url).pathname) || req.mode === 'navigate';
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  if (fresh(e.request)){
    e.respondWith(caches.open(CACHE).then(c => {
      const net = fetch(e.request, {cache: 'no-store'}).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; });
      const slow = new Promise(res => setTimeout(res, 3500)).then(() => c.match(e.request, {ignoreSearch: true}));
      return Promise.race([net, slow.then(h => h || net)]).then(r => r || net).catch(() => c.match(e.request, {ignoreSearch: true}).then(h => h || c.match('./index.html')));
    }));
    return;
  }
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(e.request, {ignoreSearch: true});
    const net = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  }));
});
