// public/service-worker.js - Alpacar PWA Service Worker

const SW_VERSION = "v3.0";
const CACHE_NAME = `alpacar-cache-${SW_VERSION}`;
const precacheResources = ['/', '/index.html'];

// 푸시 알림 관련 상수
const NOTIFICATION_SETTINGS = {
  parking: {
    title: "🚗 주차 알림",
    icon: "/alpaca-logo-small.png",
    badge: "/alpaca-logo-small.png",
    tag: "parking-notification"
  },
  entry: {
    title: "🅿️ 입차 완료",
    icon: "/alpaca-logo-small.png", 
    badge: "/alpaca-logo-small.png",
    tag: "entry-notification"
  },
  exit: {
    title: "🚪 출차 완료",
    icon: "/alpaca-logo-small.png",
    badge: "/alpaca-logo-small.png", 
    tag: "exit-notification"
  },
  warning: {
    title: "⚠️ 주차 경고",
    icon: "/alpaca-logo-small.png",
    badge: "/alpaca-logo-small.png",
    tag: "warning-notification"
  }
};

self.addEventListener("install", (event) => {
	console.log(`Alpacar Service Worker 설치 완료 (${SW_VERSION})`);
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => cache.addAll(precacheResources))
	);
	self.skipWaiting();
});

self.addEventListener("activate", (event) => {
	console.log(`Alpacar Service Worker 활성화 완료 (${SW_VERSION})`);
	event.waitUntil(
		caches.keys().then((cacheNames) => {
			return Promise.all(
				cacheNames.map((cacheName) => {
					if (cacheName !== CACHE_NAME) {
						console.log('이전 캐시 삭제:', cacheName);
						return caches.delete(cacheName);
					}
				})
			);
		}).then(() => {
			return self.clients.claim();
		})
	);
});

self.addEventListener("fetch", (event) => {
	event.respondWith(
		(async () => {
			try {
				// API 요청은 항상 네트워크에서 가져오기
				if (event.request.url.includes("/api/")) {
					return await fetch(event.request);
				}
				
				// 캐시 우선 전략 with 오프라인 fallback
				const cached = await caches.match(event.request);
				if (cached) {
					console.log('캐시에서 제공:', event.request.url);
					return cached;
				}
				
				// 네트워크에서 가져와서 캐시에 저장
				const response = await fetch(event.request);
				if (response.status === 200 && response.type === 'basic') {
					const cache = await caches.open(CACHE_NAME);
					console.log('캐시에 저장:', event.request.url);
					cache.put(event.request, response.clone());
				}
				return response;
			} catch (err) {
				console.error("SW fetch error:", err);
				
				// 오프라인 상태에서 캐시된 리소스 반환
				const cached = await caches.match(event.request);
				if (cached) {
					console.log('오프라인 - 캐시에서 제공:', event.request.url);
					return cached;
				}
				
				// HTML 요청의 경우 오프라인 페이지 반환
				if (event.request.destination === 'document') {
					const offlineResponse = await caches.match('/');
					if (offlineResponse) {
						return offlineResponse;
					}
				}
				
				return new Response('오프라인 상태입니다.', { 
					status: 503, 
					statusText: "Service Unavailable",
					headers: { 'Content-Type': 'text/plain; charset=utf-8' }
				});
			}
		})()
	);
});

// 푸시 알림 수신 처리
self.addEventListener("push", (event) => {
	console.log('푸시 알림 수신:', event);
	
	let notificationData = {
		type: 'general',
		title: 'Alpacar 알림',
		body: '새로운 알림이 있습니다.',
		data: {}
	};

	if (event.data) {
		try {
			notificationData = event.data.json();
		} catch (e) {
			console.error('푸시 데이터 파싱 오류:', e);
		}
	}

	const options = getNotificationOptions(notificationData);
	
	event.waitUntil(
		self.registration.showNotification(options.title, options)
	);
});

// 알림 클릭 처리
self.addEventListener("notificationclick", (event) => {
	console.log('알림 클릭:', event);
	
	event.notification.close();
	
	const notificationData = event.notification.data || {};
	let urlToOpen = '/';
	
	// 알림 타입에 따른 URL 결정
	switch (notificationData.type) {
		case 'parking':
		case 'entry':
		case 'exit':
			urlToOpen = '/parking-history';
			break;
		case 'warning':
			urlToOpen = '/main';
			break;
		default:
			urlToOpen = '/';
	}
	
	event.waitUntil(
		clients.matchAll({ type: 'window', includeUncontrolled: true })
			.then((clientList) => {
				// 이미 열린 탭이 있으면 해당 탭으로 이동
				for (const client of clientList) {
					if (client.url === self.location.origin + urlToOpen && 'focus' in client) {
						return client.focus();
					}
				}
				// 열린 탭이 없으면 새 탭 열기
				if (clients.openWindow) {
					return clients.openWindow(urlToOpen);
				}
			})
	);
});

// 알림 옵션 생성 함수
function getNotificationOptions(data) {
	const type = data.type || 'general';
	const settings = NOTIFICATION_SETTINGS[type] || NOTIFICATION_SETTINGS.parking;
	
	return {
		title: data.title || settings.title,
		body: data.body || data.message || '새로운 알림이 있습니다.',
		icon: settings.icon,
		badge: settings.badge,
		tag: settings.tag,
		data: data,
		actions: [
			{
				action: 'view',
				title: '확인'
			},
			{
				action: 'close', 
				title: '닫기'
			}
		],
		requireInteraction: data.requireInteraction || false,
		silent: false,
		vibrate: [200, 100, 200]
	};
}

// 백그라운드 동기화 (선택적)
self.addEventListener('sync', (event) => {
	console.log('백그라운드 동기화:', event.tag);
	
	if (event.tag === 'parking-sync') {
		event.waitUntil(syncParkingData());
	}
});

// 주차 데이터 동기화 함수
async function syncParkingData() {
	try {
		// 오프라인에서 저장된 주차 데이터를 서버와 동기화
		console.log('주차 데이터 백그라운드 동기화 시작');
		// 실제 구현은 백엔드 API와 연동하여 처리
	} catch (error) {
		console.error('주차 데이터 동기화 실패:', error);
	}
}
