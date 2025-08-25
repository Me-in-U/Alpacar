// src/main.ts
import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";
import { useUserStore } from "@/stores/user";
import { registerServiceWorker, subscribeToPushNotifications } from "@/utils/pwa";
import { SecureTokenManager } from "@/utils/security";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

// 앱 시작 시 한 번만 실행 (로그인 페이지가 아닐 때만)
const userStore = useUserStore();
const isLoginPage = window.location.pathname === "/login" || window.location.pathname === "/";

// 사용자 정보 복원 시도
const restoredUser = userStore.restoreUserFromStorage();

// API 호출 중복 방지를 위한 플래그
let isInitializing = false;

// 전역 에러 핸들러(세션 만료만 특별 처리)
function handleInitError(err: any) {
	const userStore = useUserStore();
	if (err?.code === "SESSION_EXPIRED") {
		// 인터셉터(refresh 실패)가 설정한 코드
		userStore.clearUser();
		// TODO: 토스트 표시: "세션이 만료되었습니다. 다시 로그인해주세요."
		router.replace("/login");
		return true; // handled
	}
	return false; // not handled
}

if (!isLoginPage) {
	// 보안 토큰 관리자에서 토큰 가져오기
	const token = SecureTokenManager.getSecureToken("access_token");
	if (token && !isInitializing) {
		isInitializing = true;

		// 복원된 사용자 정보가 있으면 API 호출 지연
		const delayTime = restoredUser ? 500 : 0;

		setTimeout(async () => {
			try {
				await userStore.fetchMe(token);
				console.log("사용자 정보 로드 성공");

				// 차량 정보도 미리 로드 (라우터 가드 성능 개선)
				try {
					await userStore.fetchMyVehicles();
					console.log("앱 초기화 시 차량 정보 미리 로드 완료");
				} catch (vehicleError) {
					console.warn("차량 정보 로드 실패 (무시):", vehicleError);
				}
			} catch (error: any) {
				console.warn("사용자 정보 로드 실패:", error);

				// ✅ 1순위: refresh 실패(진짜 만료)만 특별 처리
				if (handleInitError(error)) {
					// 처리됨(로그아웃/리다이렉트 완료)
				} else {
					// ⛳ 2순위: 기존 호환(문자열로 401/403 판단하던 로직 유지)
					if (typeof error?.message === "string" && (error.message.includes("401") || error.message.includes("403"))) {
						const isExpired = await userStore.checkAutoLoginExpiry();
						if (isExpired) {
							userStore.clearUser();
							router.push("/login");
						}
					} else {
						// 네트워크/서버 에러는 복원된 정보 유지
						console.log("네트워크/서버 에러로 인한 실패 - 기존 세션 유지");
					}
				}
			} finally {
				isInitializing = false;
			}
		}, delayTime);
	} else if (!restoredUser && !token) {
		// 토큰도 없고 복원된 사용자 정보도 없으면 로그인 페이지로
		router.push("/login");
	}
}

app.mount("#app");

// PWA 및 푸시 알림 초기화
let deferredPrompt: any = null;

// PWA 설치 프롬프트 캐치
window.addEventListener("beforeinstallprompt", (e) => {
	console.log("PWA 설치 프롬프트 감지");
	e.preventDefault();
	deferredPrompt = e;
});

// PWA 설치 완료 감지
window.addEventListener("appinstalled", () => {
	console.log("PWA 설치 완료");
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
			const token = SecureTokenManager.getSecureToken("access_token");

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
			if (choiceResult.outcome === "accepted") {
				console.log("사용자가 PWA 설치를 승인");
			}
			deferredPrompt = null;
		});
	} else {
		console.log("PWA 설치 프롬프트를 사용할 수 없습니다");
	}
};
