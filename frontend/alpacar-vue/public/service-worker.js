// public/service-worker.js - Alpacar PWA Service Worker (safe fetch)
const SW_VERSION = "v3.3";
const CACHE_NAME = `alpacar-cache-${SW_VERSION}`;
const precacheResources = ["/", "/index.html"];

const NOTIFICATION_SETTINGS = {
	parking: { title: "🚗 주차 알림", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "parking-notification" },
	entry: { title: "🅿️ 입차 완료", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "entry-notification" },
	exit: { title: "🚪 출차 완료", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "exit-notification" },
	warning: { title: "⚠️ 주차 경고", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "warning-notification" },
};

self.addEventListener("install", (event) => {
	console.log(`Alpacar SW install ${SW_VERSION}`);
	event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(precacheResources)));
	self.skipWaiting();
});

self.addEventListener("activate", (event) => {
	console.log(`Alpacar SW activate ${SW_VERSION}`);
	event.waitUntil(
		caches
			.keys()
			.then((names) => Promise.all(names.map((n) => (n !== CACHE_NAME ? caches.delete(n) : undefined))))
			.then(() => self.clients.claim())
	);
});

// ---- 핵심 수정: 안전한 fetch 핸들러 ----
self.addEventListener("fetch", (event) => {
	const req = event.request;
	const url = new URL(req.url);

	// 1) http/https만 처리 (chrome-extension, ws, wss 등은 무시)
	if (url.protocol !== "http:" && url.protocol !== "https:") {
		return; // 그냥 브라우저 기본 처리
	}

	// 2) API는 항상 네트워크로
	if (url.pathname.startsWith("/api/")) {
		event.respondWith(fetch(req).catch(() => new Response("오프라인입니다.", { status: 503 })));
		return;
	}

	// 3) GET만 캐싱 (POST/PUT 등은 네트워크로)
	if (req.method !== "GET") {
		event.respondWith(fetch(req));
		return;
	}

	// 4) 다른 오리진은 네트워크 우선 (원하면 캐시 제외)
	const sameOrigin = url.origin === self.location.origin;

	event.respondWith(
		(async () => {
			try {
				// 같은 오리진 정적 리소스: 캐시 우선 + 네트워크 갱신
				if (sameOrigin) {
					const cached = await caches.match(req);
					if (cached) {
						// 백그라운드로 최신화 시도(실패해도 OK)
						fetch(req)
							.then(async (res) => {
								if (res && res.status === 200 && res.type === "basic") {
									try {
										const cache = await caches.open(CACHE_NAME);
										await cache.put(req, res.clone());
									} catch (e) {
										// ignore cache put failure
									}
								}
							})
							.catch(() => {});
						return cached;
					}

					const res = await fetch(req);
					if (res && res.status === 200 && res.type === "basic") {
						try {
							const cache = await caches.open(CACHE_NAME);
							await cache.put(req, res.clone());
						} catch (e) {
							// ignore
						}
					}
					return res;
				}

				// 다른 오리진: 네트워크 우선 (캐시에는 넣지 않음)
				return await fetch(req);
			} catch (err) {
				// 오프라인 fallback
				const cached = await caches.match(req);
				if (cached) return cached;

				if (req.destination === "document") {
					const offline = await caches.match("/");
					if (offline) return offline;
				}
				return new Response("오프라인 상태입니다.", {
					status: 503,
					statusText: "Service Unavailable",
					headers: { "Content-Type": "text/plain; charset=utf-8" },
				});
			}
		})()
	);
});

// ---- push / notificationclick / sync 는 동일 ----
self.addEventListener("push", (event) => {
	let data = { type: "general", title: "Alpacar 알림", body: "새로운 알림이 있습니다.", data: {} };
	if (event.data) {
		try {
			data = event.data.json();
		} catch {}
	}
	const opt = getNotificationOptions(data);
	event.waitUntil(self.registration.showNotification(opt.title, opt));
});

self.addEventListener("notificationclick", (event) => {
	event.notification.close();
	const data = event.notification.data || {};
	let urlToOpen = "/";
	switch (data.type) {
		case "parking":
		case "entry":
		case "exit":
			urlToOpen = "/parking-history";
			break;
		case "warning":
			urlToOpen = "/main";
			break;
	}
	event.waitUntil(
		clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
			for (const c of list) {
				if (c.url === self.location.origin + urlToOpen && "focus" in c) return c.focus();
			}
			if (clients.openWindow) return clients.openWindow(urlToOpen);
		})
	);
});

function getNotificationOptions(data) {
	const s = NOTIFICATION_SETTINGS[data.type] || NOTIFICATION_SETTINGS.parking;
	return {
		title: data.title || s.title,
		body: data.body || data.message || "새로운 알림이 있습니다.",
		icon: s.icon,
		badge: s.badge,
		tag: s.tag,
		data,
		actions: [
			{ action: "view", title: "확인" },
			{ action: "close", title: "닫기" },
		],
		requireInteraction: !!data.requireInteraction,
		silent: false,
		vibrate: [200, 100, 200],
	};
}

self.addEventListener("sync", (event) => {
	if (event.tag === "parking-sync") event.waitUntil(syncParkingData());
});

async function syncParkingData() {
	try {
		// TODO: 오프라인 큐 → 서버 동기화
		console.log("주차 데이터 백그라운드 동기화");
	} catch (e) {
		console.error("동기화 실패:", e);
	}
}
