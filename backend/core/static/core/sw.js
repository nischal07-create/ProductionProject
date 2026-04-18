const CACHE_NAME = "trailmate-offline-v2";
const CORE_ASSETS = [
  "/api/trips/trekking/routes/",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).catch(() => Promise.resolve())
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isTrekMapAsset = url.pathname.startsWith("/static/core/maps/");
  const isTrekApi = url.pathname.startsWith("/api/trips/trekking/routes/");

  if (isTrekMapAsset || isTrekApi) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        const network = fetch(event.request)
          .then((response) => {
            if (response && response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
            }
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  if (event.request.mode === "navigate") {
    event.respondWith(fetch(event.request));
  }
});
