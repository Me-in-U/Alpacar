// public/service-worker.js - Alpacar PWA Service Worker (safe fetch)
// ✅ Workbox 프리캐시 주입 지점 (빌드 시 자동으로 매니페스트 주입됨)
const precacheManifest = self.__WB_MANIFEST || [];

const SW_VERSION = "v3.5";
const CACHE_NAME = `alpacar-cache-${SW_VERSION}`;
const precacheResources = ["/", "/index.html"];

// Workbox 매니페스트와 기본 리소스 결합
const allPrecacheResources = [...precacheResources, ...precacheManifest.map((entry) => (typeof entry === "string" ? entry : entry.url))];

const NOTIFICATION_SETTINGS = {
	parking_assigned: { title: "🚗 주차 배정", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "parking-assigned-notification" },
	parking_complete: { title: "🅿️ 주차 완료", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "parking-complete-notification" },
	entry: { title: "🚪 입차 완료", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "entry-notification" },
	exit: { title: "🚗 출차 완료", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "exit-notification" },
	warning: { title: "⚠️ 주차 경고", icon: "/alpaca-192.png", badge: "/alpaca-192.png", tag: "warning-notification" },
};

self.addEventListener("install", (event) => {
	console.log(`Alpacar SW install ${SW_VERSION}`);
	console.log(`Precaching ${allPrecacheResources.length} resources`);
	event.waitUntil(
		caches.open(CACHE_NAME).then(async (cache) => {
			// 중복 제거: Set을 사용하여 중복 URL 제거
			const uniqueResources = [...new Set(allPrecacheResources)];
			console.log(`Unique resources: ${uniqueResources.length}`);

			// 하나씩 추가하여 중복 에러 방지
			for (const resource of uniqueResources) {
				try {
					await cache.add(resource);
				} catch (error) {
					console.warn(`Failed to cache ${resource}:`, error);
				}
			}
		})
	);
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

	//v3.4
	// 1.5) OAuth 관련 경로/쿼리는 무조건 네트워크 통과 (캐시 금지)
	// const OAUTH_PATH = /\/(auth|oauth|login|signin|logout|callback|accounts)\b/i;
	// const OAUTH_QUERY_KEYS = ["state", "code", "g_state", "scope", "prompt", "authuser", "hd"];
	// const hasOAuthQuery = OAUTH_QUERY_KEYS.some((k) => url.searchParams.has(k));
	// if (OAUTH_PATH.test(url.pathname) || hasOAuthQuery) {
	// 	event.respondWith(fetch(req).catch(() => new Response("오프라인입니다.", { status: 503 })));
	// 	return;
	// }
	// ✅ 1.0) OAuth 콜백은 '완전 우회'(가로채지 않음) — 브라우저 기본 리다이렉트/네비 처리
	//    * 백엔드 콜백(토큰 발급/302): /api/auth/social/google/callback/
	//    * 프론트 콜백(쿼리 파싱):     /auth/social/google/callback
	const BYPASS_PATHS = ["/api/auth/social/google/callback/", "/auth/social/google/callback"];
	if (BYPASS_PATHS.some((p) => url.pathname.startsWith(p))) {
		return; // event.respondWith 호출 금지 => 브라우저가 직접 처리
	}

	// (선택) state/code 등 OAuth 쿼리가 있으면 우회
	const OAUTH_QUERY_KEYS = ["state", "code", "g_state", "scope", "prompt", "authuser", "hd"];
	const hasOAuthQuery = OAUTH_QUERY_KEYS.some((k) => url.searchParams.has(k));
	if (hasOAuthQuery) return;

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

	// 3.5) 문서 네비게이션은 네트워크 우선(오프라인 시 홈 fallback)
	if (req.mode === "navigate" || req.destination === "document") {
		event.respondWith(
			(async () => {
				try {
					return await fetch(req); // 항상 최신 앱 상태
				} catch {
					const cachedHome = await caches.match("/");
					return cachedHome || new Response("오프라인 상태입니다.", { status: 503 });
				}
			})()
		);
		return;
	}

	// 4) 다른 오리진은 네트워크 우선 (원하면 캐시 제외)
	const sameOrigin = url.origin === self.location.origin;

	event.respondWith(
		(async () => {
			try {
				// 같은 오리진 "정적 리소스"만 캐시 (그 외는 네트워크)
				if (sameOrigin) {
					const isStatic = /\.(?:js|css|png|jpe?g|svg|webp|ico|woff2?|ttf|map)$/.test(url.pathname);

					if (isStatic) {
						const cached = await caches.match(req);
						if (cached) {
							// 백그라운드 최신화
							fetch(req)
								.then(async (res) => {
									if (res && res.ok && res.type === "basic") {
										const cache = await caches.open(CACHE_NAME);
										await cache.put(req, res.clone());
									}
								})
								.catch(() => {});
							return cached;
						}
						const res = await fetch(req);
						if (res && res.ok && res.type === "basic") {
							const cache = await caches.open(CACHE_NAME);
							await cache.put(req, res.clone());
						}
						return res;
					}
				}
				// 정적이 아니거나 다른 오리진: 네트워크 우선(캐시 X)
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
		case "parking_assigned":
			urlToOpen = "/parking-recommend";
			break;
		case "parking_complete":
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
	const s = NOTIFICATION_SETTINGS[data.type] || NOTIFICATION_SETTINGS.parking_assigned;
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
