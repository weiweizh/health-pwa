// Service Worker for Health Check-in PWA
const CACHE_NAME = 'health-pwa-v1';
const urlsToCache = [
    'health-pwa.html',
    'manifest.json',
    '/'
];

// Install event - cache essential files
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            // Try to cache files, but don't fail if some are missing
            return Promise.allSettled(
                urlsToCache.map(url => {
                    return cache.add(url).catch(() => {
                        // Silently ignore failed cache attempts
                    });
                })
            );
        })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - network first with cache fallback
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // For CDN resources (Chart.js, fonts, etc.), use network first
    if (event.request.url.includes('cdn.') ||
        event.request.url.includes('fonts.googleapis') ||
        event.request.url.includes('fonts.gstatic')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    // Clone the response and cache it
                    if (response.ok) {
                        const cacheResponse = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, cacheResponse);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Fall back to cache if network fails
                    return caches.match(event.request);
                })
        );
    } else {
        // For local resources, use cache first with network fallback
        event.respondWith(
            caches.match(event.request).then((response) => {
                return response || fetch(event.request)
                    .then((response) => {
                        // Cache successful responses
                        if (response.ok) {
                            const cacheResponse = response.clone();
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(event.request, cacheResponse);
                            });
                        }
                        return response;
                    })
                    .catch(() => {
                        // Return cached response if fetch fails
                        return caches.match(event.request);
                    });
            })
        );
    }
});

// Background sync for future use (optional)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-health-data') {
        event.waitUntil(
            // Implement data sync if needed
            Promise.resolve()
        );
    }
});
