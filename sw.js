/* OPRUIMER — geen cache meer.
 * Eerdere versies gebruikten een service worker die de app op het apparaat
 * cachte; dat hield oude/kapotte versies vast. Deze versie doet het tegenovergestelde:
 * hij wist alle caches en verwijdert zichzelf, zodat de app voortaan ALTIJD
 * rechtstreeks en vers van de server komt. Cruciaal voor een trading-app.
 */
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
    await self.registration.unregister();
    const clients = await self.clients.matchAll();
    clients.forEach((c) => c.navigate(c.url)); // herlaad met verse bestanden
  })());
});
