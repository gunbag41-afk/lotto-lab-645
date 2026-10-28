const CACHE='lotto-lab-645-v2.2';
const CORE=['./','./index.html','./styles.css','./app.js','./manifest.webmanifest','./icon.svg','./icon-192.png','./icon-512.png'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE)));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',event=>{const req=event.request;if(req.method!=='GET'||new URL(req.url).origin!==self.location.origin)return;
 const url=new URL(req.url);if(url.pathname.endsWith('/data/draws.json')){event.respondWith(fetch(req).then(res=>{if(res.ok){const clone=res.clone();caches.open(CACHE).then(cache=>cache.put(req,clone));}return res;}).catch(()=>caches.match(req)));return;}
 event.respondWith(fetch(req).then(res=>{if(res.ok&&CORE.some(path=>new URL(path,self.registration.scope).pathname===url.pathname)){const c=res.clone();caches.open(CACHE).then(cache=>cache.put(req,c));}return res;}).catch(()=>caches.match(req).then(r=>r||caches.match('./index.html'))));});
