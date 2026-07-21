// Service Worker for Health Check-in PWA
const CACHE_NAME = 'health-pwa-v3';
const urlsToCache = [
    'index.html',
    'manifest.json',
    '/'
];

// Install — pre-cache essentials, then take over immediately.
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return Promise.allSettled(
                urlsToCache.map((url) => cache.add(url).catch(() => {}))
            );
        })
    );
    self.skipWaiting();
});

// Activate — delete old caches so a new deploy replaces the stale HTML.
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((names) => Promise.all(
            names.map((name) => name !== CACHE_NAME ? caches.delete(name) : null)
        ))
    );
    self.clients.claim();
});

function networkFirst(request) {
    return fetch(request)
        .then((response) => {
            if (response && response.ok) {
                const copy = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
            }
            return response;
        })
        .catch(() => caches.match(request));
}

function cacheFirst(request) {
    return caches.match(request).then((cached) => {
        return cached || fetch(request).then((response) => {
            if (response && response.ok) {
                const copy = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
            }
            return response;
        }).catch(() => cached);
    });
}

// Fetch strategy:
//  - HTML documents (the app itself): NETWORK FIRST, so a new deploy is picked
//    up as soon as the device is online, with the cached copy as offline fallback.
//    (Cache-first here is what pinned users to a stale index.html.)
//  - CDN assets (Chart.js, fonts): network first, cache fallback.
//  - Other local assets (manifest, etc.): cache first for speed.
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;

    const url = event.request.url;
    const isHTML = event.request.mode === 'navigate' ||
                   url.endsWith('.html') ||
                   url.endsWith('/');

    if (isHTML) {
        event.respondWith(networkFirst(event.request));
    } else if (url.includes('cdn.') ||
               url.includes('fonts.googleapis') ||
               url.includes('fonts.gstatic')) {
        event.respondWith(networkFirst(event.request));
    } else {
        event.respondWith(cacheFirst(event.request));
    }
});
