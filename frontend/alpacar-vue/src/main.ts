// main.ts
import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";
import { useUserStore } from "@/stores/user";
import { registerServiceWorker, subscribeToPushNotifications } from "@/utils/pwa";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

// 앱 시작 시 한 번만 실행 (로그인 페이지가 아닐 때만)
const userStore = useUserStore();
const isLoginPage = window.location.pathname === '/login' || window.location.pathname === '/';
if (!isLoginPage) {
	const token = localStorage.getItem("access_token");
	if (token) {
		userStore.fetchMe(token).catch(() => {
			// 토큰이 만료됐거나 오류가 나면 로그인 페이지로
			userStore.clearUser();
			router.push("/login");
		});
	}
}

app.mount("#app");

// PWA 및 푸시 알림 초기화
let deferredPrompt: any = null;

// PWA 설치 프롬프트 캐치
window.addEventListener('beforeinstallprompt', (e) => {
	console.log('PWA 설치 프롬프트 감지');
	e.preventDefault();
	deferredPrompt = e;
	
	// PWA 설치 버튼을 표시할 수 있음
	// (선택적으로 UI에서 설치 버튼 활성화)
});

// PWA 설치 완료 감지
window.addEventListener('appinstalled', () => {
	console.log('PWA 설치 완료');
	deferredPrompt = null;
});

// Service Worker 및 푸시 알림 초기화
window.addEventListener("load", async () => {
	try {
		// Service Worker 등록
		const registration = await registerServiceWorker();
		
		if (registration) {
			console.log("Alpacar PWA Service Worker 등록 성공");
			
			// 로그인된 사용자의 경우에만 푸시 알림 구독 시도 (로그인 페이지 제외)
			const isLoginPage = window.location.pathname === '/login' || window.location.pathname === '/';
			const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
			
			if (token && !isLoginPage) {
				// 페이지 로드 후 3초 뒤에 알림 권한 요청 (사용자 경험 개선)
				setTimeout(async () => {
					try {
						await subscribeToPushNotifications();
						console.log("푸시 알림 구독 완료");
					} catch (error) {
						console.log("푸시 알림 구독 선택사항이므로 건너뛰기:", error);
					}
				}, 3000);
			} else if (isLoginPage) {
				console.log("로그인 페이지에서는 푸시 알림 초기화 건너뛰기");
			}
		}
	} catch (error) {
		console.error("PWA 초기화 오류:", error);
	}
});

// PWA 설치 프롬프트 전역 함수로 노출
(window as any).promptPWAInstall = () => {
	if (deferredPrompt) {
		deferredPrompt.prompt();
		deferredPrompt.userChoice.then((choiceResult: any) => {
			if (choiceResult.outcome === 'accepted') {
				console.log('사용자가 PWA 설치를 승인');
			}
			deferredPrompt = null;
		});
	} else {
		console.log('PWA 설치 프롬프트를 사용할 수 없습니다');
	}
};
