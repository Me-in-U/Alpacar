// public/service-worker.js

const SW_VERSION = "v2";

self.addEventListener("install", (event) => {
	console.log(`Service Worker 설치 완료(${SW_VERSION})`);
	// 예: 캐시 초기화
});

self.addEventListener("activate", (event) => {
	event.waitUntil(self.clients.claim()); // 즉시 페이지 컨트롤
	console.log(`Service Worker 활성화 완료(${SW_VERSION})`);
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
