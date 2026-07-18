// Vuelto service worker — auto-update: HTML siempre fresco, assets desde cache
const C = 'vuelto-v2';
const SHELL = ['./', './index.html', './icon.png', './manifest.json', './og.png'];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(C).then(c => c.addAll(SHELL)));
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    // borrar caches viejos (versiones anteriores)
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== C).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const isHTML = req.mode === 'navigate' ||
    (req.headers.get('accept') || '').includes('text/html');

  if (isHTML) {
    // network-first: siempre intenta traer la última versión; offline usa cache
    e.respondWith(
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(C).then(c => c.put('./index.html', copy));
        return res;
      }).catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
  } else {
    // assets: cache-first (rápido), con actualización en segundo plano
    e.respondWith(
      caches.match(req).then(cached => {
        const net = fetch(req).then(res => {
          caches.open(C).then(c => c.put(req, res.clone()));
          return res;
        }).catch(() => cached);
        return cached || net;
      })
    );
  }
});
