'use strict';
const CACHE='athena-shell-v2';
const SHELL=['/','/manifest.webmanifest','/static/style.css','/static/fonts.css','/static/app.js','/static/icon.svg','/static/icon-192.svg','/static/icon-512.svg'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin)return;
  const isShell=request.mode==='navigate'||url.pathname==='/manifest.webmanifest'||url.pathname.startsWith('/static/');
  if(!isShell)return;
  event.respondWith(fetch(request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(request,copy));}return response;}).catch(()=>caches.match(request).then(cached=>cached||caches.match('/'))));
});
