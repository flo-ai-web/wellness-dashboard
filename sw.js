// Minimaler Service Worker - kein Caching, nur PWA-Voraussetzung erfüllen
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
