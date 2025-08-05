// public/service-worker.js
self.addEventListener("install", (event) => {
	console.log("Service Worker 설치 완료");
	// 예: 캐시 초기화
});

self.addEventListener("activate", (event) => {
	console.log("Service Worker 활성화 완료");
});

self.addEventListener("fetch", (event) => {
	// 예: 네트워크 우선, 실패 시 캐시
	event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
// static/service-worker.js
self.addEventListener("push", (event) => {
	let data = {};
	if (event.data) {
		data = event.data.json();
	}
	event.waitUntil(
		self.registration.showNotification(data.title || "OCR 알림", {
			body: data.body || "",
			icon: "/static/icons/favicon.ico",
		})
	);
});
