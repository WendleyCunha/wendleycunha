// King Star Portal — Service Worker v1.0
const CACHE_NAME = 'kingstar-portal-v1';

// Recursos que serão cacheados na instalação
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
];

// ── INSTALL: cacheia os recursos estáticos ──────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ── ACTIVATE: remove caches antigos ────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// ── FETCH: estratégia Network First com fallback para cache ────────────────
self.addEventListener('fetch', event => {
  // Ignora requisições de outros domínios (CDN, APIs externas)
  if (!event.request.url.startsWith(self.location.origin)) return;

  // Ignora métodos não-GET
  if (event.request.method !== 'GET') return;

  // Para requisições de assets estáticos: Cache First
  if (
    event.request.url.includes('/static/') ||
    event.request.url.includes('.css') ||
    event.request.url.includes('.js') ||
    event.request.url.includes('.png') ||
    event.request.url.includes('.ico')
  ) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        });
      })
    );
    return;
  }

  // Para o app principal: Network First (garante dados frescos)
  event.respondWith(
    fetch(event.request)
      .then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// ── PUSH NOTIFICATIONS (base para futuras notificações) ────────────────────
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'King Star Colchões';
  const options = {
    body: data.body || 'Você tem uma atualização no portal.',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    data: { url: data.url || '/' },
    actions: [
      { action: 'open', title: 'Ver agora' },
      { action: 'close', title: 'Fechar' }
    ]
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'open') {
    event.waitUntil(clients.openWindow(event.notification.data.url));
  }
});
