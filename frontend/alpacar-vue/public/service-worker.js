// public/service-worker.js
self.addEventListener("install", (event) => {
	console.log("Service Worker 설치 완료");
	// 예: 캐시 초기화
});

self.addEventListener("activate", (event) => {
	console.log("Service Worker 활성화 완료");
});

self.addEventListener("fetch", (event) => {
	event.respondWith(
		(async () => {
			try {
				if (event.request.url.includes("/api/")) {
					return await fetch(event.request);
				}
				const cached = await caches.match(event.request);
				return cached || (await fetch(event.request));
			} catch (err) {
				console.error("SW fetch error:", err);
				// 네트워크·캐시 모두 실패 시 빈 Response 리턴
				return new Response(null, { status: 504, statusText: "SW_GATEWAY_TIMEOUT" });
			}
		})()
	);
});

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
