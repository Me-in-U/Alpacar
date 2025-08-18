import { createRouter, createWebHistory } from "vue-router";

// 라우터 메타 타입 정의
declare module "vue-router" {
	interface RouteMeta {
		requiresAuth?: boolean;
		requiresPasswordAuth?: boolean;
	}
}
import EntryPage from "@/views/user/EntryPage.vue";
import Login from "@/views/user/Login.vue";
import Signup from "@/views/user/Signup.vue";
import ForgotPassword from "@/views/user/ForgotPassword.vue";
import SocialLoginInfo from "@/views/user/SocialLoginInfo.vue";
import MainPage from "@/views/user/MainPage.vue";
import UserProfile from "@/views/user/UserProfile.vue";
import AdminLogin from "@/views/admin/AdminLogin.vue";
import AdminMain from "@/views/admin/AdminMain.vue";
import AdminParkingLogs from "@/views/admin/AdminParkingLogs.vue";
import AdminPlateOcr from "@/views/admin/AdminPlateOcr.vue";
import ParkingRecommend from "@/views/user/ParkingRecommend.vue";
import ParkingComplete from "@/views/user/ParkingComplete.vue";
import ParkingHistory from "@/views/user/ParkingHistory.vue";
import ModalTest from "@/views/user/ModalTest.vue";
import AdminErrorModalTest from "@/views/admin/AdminErrorModalTest.vue";
import GoogleCallback from "@/views/user/GoogleCallback.vue";
import MainWithHolo from "@/views/user/MainWithHolo.vue";
import AlertTest from "@/views/test/AlertTest.vue";
import { BACKEND_BASE_URL } from "@/utils/api";
import { useUserStore } from "@/stores/user";
import { SecureTokenManager } from "@/utils/security";
import UserSetting from "@/views/user/UserSetting.vue";


// 보안 강화된 로그인 상태 확인 함수
async function isAuthenticated(): Promise<boolean> {
	try {
		const userStore = useUserStore();
		
		// 먼저 사용자 정보가 복원되었는지 확인
		if (!userStore.me) {
			const restoredUser = userStore.restoreUserFromStorage();
			if (restoredUser) {
				console.log("라우터에서 사용자 정보 복원:", restoredUser);
			}
		}
		
		// 보안 토큰 매니저에서 토큰 확인
		const token = SecureTokenManager.getSecureToken("access_token");

		// 모바일 환경 호환성: 토큰이 없으면 즉시 false 반환
		if (!token) {
			console.log("[AUTH CHECK] 토큰 없음 - 인증 실패");
			return false;
		}

		// 복원된 사용자 정보도 있어야 완전한 인증으로 간주
		if (!userStore.me) {
			console.log("[AUTH CHECK] 사용자 정보 없음 - 인증 불완전");
			return false;
		}

		// 자동 로그인인 경우 만료 여부 확인 (토큰이 있을 때만)
		if (token) {
			const expiryDate = localStorage.getItem("auto_login_expiry");
			if (expiryDate) {
				const isExpired = await userStore.checkAutoLoginExpiry();
				if (isExpired) {
					return false;
				}
			}
		}

		return true;
	} catch (error) {
		console.warn("Authentication check failed:", error);
		// 에러 발생 시에도 복원된 사용자 정보가 있으면 인증된 것으로 간주
		const userStore = useUserStore();
		return !!userStore.me;
	}
}

// 차량 등록 여부 확인 함수 (모바일 환경 개선)
async function hasVehicleRegistered(): Promise<boolean> {
	const token = SecureTokenManager.getSecureToken("access_token");
	if (!token) {
		console.log("[VEHICLE CHECK] 토큰 없음");
		return false;
	}

	// 캐시된 결과 확인 (5분간 유효)
	const cached = sessionStorage.getItem("vehicle_check_cache");
	if (cached) {
		try {
			const { result, timestamp } = JSON.parse(cached);
			const now = Date.now();
			if (now - timestamp < 5 * 60 * 1000) { // 5분
				console.log("[VEHICLE CHECK] 캐시된 결과 사용:", result);
				return result;
			}
		} catch (e) {
			sessionStorage.removeItem("vehicle_check_cache");
		}
	}

	// 재시도 로직으로 API 호출
	let lastError: any = null;
	for (let attempt = 1; attempt <= 3; attempt++) {
		try {
			console.log(`[VEHICLE CHECK] API 호출 시도 ${attempt}/3`);
			
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), 8000); // 8초 타임아웃
			
			const response = await fetch(`${BACKEND_BASE_URL}/vehicles/check/`, {
				method: "GET",
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "application/json",
				},
				signal: controller.signal,
				cache: "no-cache",
			});

			clearTimeout(timeoutId);

			if (response.ok) {
				const data = await response.json();
				const result = data.has_vehicle ?? false;
				
				// 성공 시 결과 캐시
				sessionStorage.setItem("vehicle_check_cache", JSON.stringify({
					result,
					timestamp: Date.now()
				}));
				
				console.log(`[VEHICLE CHECK] API 성공 (시도 ${attempt}):`, result);
				return result;
			} else if (response.status === 401 || response.status === 403) {
				// 인증 오류는 재시도하지 않음
				console.log("[VEHICLE CHECK] 인증 오류, 로그인 필요");
				return false;
			} else {
				lastError = new Error(`HTTP ${response.status}`);
				console.warn(`[VEHICLE CHECK] HTTP 오류 ${response.status} (시도 ${attempt})`);
			}
		} catch (error: any) {
			lastError = error;
			if (error.name === 'AbortError') {
				console.warn(`[VEHICLE CHECK] 타임아웃 (시도 ${attempt})`);
			} else {
				console.warn(`[VEHICLE CHECK] 네트워크 오류 (시도 ${attempt}):`, error.message);
			}
		}

		// 마지막 시도가 아니면 대기 후 재시도
		if (attempt < 3) {
			await new Promise(resolve => setTimeout(resolve, 1000 * attempt)); // 1초, 2초 대기
		}
	}

	// 모든 시도 실패 시 안전한 기본값 반환
	console.error("[VEHICLE CHECK] 모든 시도 실패:", lastError?.message);
	
	// 사용자 스토어에서 기존 차량 정보 확인
	const userStore = useUserStore();
	if (userStore.vehicles && userStore.vehicles.length > 0) {
		console.log("[VEHICLE CHECK] 스토어에서 차량 정보 발견, true 반환");
		return true;
	}
	
	// 최후의 수단: 이전 성공 캐시가 있다면 사용 (만료되어도)
	if (cached) {
		try {
			const { result } = JSON.parse(cached);
			console.log("[VEHICLE CHECK] 만료된 캐시 사용:", result);
			return result;
		} catch (e) {
			// 무시
		}
	}
	
	console.warn("[VEHICLE CHECK] 기본값 false 반환 - 네트워크 문제로 추정");
	return false;
}
const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes: [
		{
			path: "/",
			name: "entry-page",
			component: EntryPage,
		},
		{
			path: "/login",
			name: "login",
			component: Login,
		},
		{
			path: "/signup",
			name: "signup",
			component: Signup,
		},
		{
			path: "/forgot-password",
			name: "forgot-password",
			component: ForgotPassword,
		},
		{
			path: "/social-login-info",
			name: "social-login-info",
			component: SocialLoginInfo,
			meta: { requiresAuth: true },
		},
		{
			path: "/main",
			name: "main",
			component: MainPage,
			meta: { requiresAuth: true },
		},
		{
			path: "/parking-history",
			name: "parking-history",
			component: ParkingHistory,
			meta: { requiresAuth: true },
		},
		{
			path: "/user-profile",
			name: "user-profile",
			component: UserProfile,
			meta: { requiresAuth: true },
		},
		{
			path: "/admin-login",
			name: "admin-login",
			component: AdminLogin,
		},
		{
			path: "/admin-main",
			name: "admin-main",
			component: AdminMain,
			meta: { requiresAuth: true },
		},
		{
			path: "/admin-parkinglogs",
			name: "admin-parkinglogs",
			component: AdminParkingLogs,
			meta: { requiresAuth: true },
		},
		{
			path: "/parking-recommend",
			name: "parking-recommend",
			component: ParkingRecommend,
			meta: { requiresAuth: true },
		},
		{
			path: "/parking-complete",
			name: "parking-complete",
			component: ParkingComplete,
			meta: { requiresAuth: true },
		},
		{
			path: "/admin-plate-ocr",
			name: "admin-plate-ocr",
			component: AdminPlateOcr,
			meta: { requiresAuth: true },
		},
		// 모달 스타일 확인용 테스트 컴포넌트
		{
			path: "/modal-test",
			name: "modal-test",
			component: ModalTest,
		},
		{
			path: "/admin-error-test",
			name: "admin-error-test",
			component: AdminErrorModalTest,
		},
		{
			path: "/auth/social/google/callback",
			name: "GoogleCallback",
			component: GoogleCallback,
		},
		//3d 모델 테스트용
		{
			path: "/holo",
			name: "holo",
			component: MainWithHolo,
		},
		{
			path: "/alert-test",
			name: "alert-test",
			component: AlertTest,
		},
		{
			path: "/user-setting",
			name: "user-setting",
			component: UserSetting,
			meta: { requiresAuth: true, requiresPasswordAuth: true },
		},
	],
});

// 네비게이션 가드 추가
router.beforeEach(async (to, from, next) => {
	const isLoggedIn = await isAuthenticated();

	console.log(`[ROUTER GUARD] 페이지 접근: ${to.path}, 로그인 상태: ${isLoggedIn}`);

	// 주차 히스토리 페이지 접근 디버그
	if (to.path === "/parking-history") {
		console.log(`[PARKING HISTORY DEBUG] 접근 시도:`, {
			path: to.path,
			isLoggedIn: isLoggedIn,
			from: from.path,
		});
	}

	// **최우선 순위: 로그인된 사용자가 관리자인 경우 접근 제어**
	if (isLoggedIn) {
		const userStore = useUserStore();

		// 사용자 정보가 없으면 보안 저장소에서 복원 시도
		if (!userStore.me) {
			const userData = userStore.restoreUserFromStorage();
			if (userData) {
				console.log(`[ROUTER GUARD] 보안 저장소에서 사용자 정보 복구:`, userData);
			}
		}

		const isAdmin = userStore.me?.is_staff ?? false;
		console.log(`[ROUTER GUARD] 관리자 여부: ${isAdmin}`, {
			user: userStore.me,
			is_staff: userStore.me?.is_staff,
			is_staff_type: typeof userStore.me?.is_staff,
		});

		// 주차 히스토리 페이지에 대한 관리자 체크 디버그
		if (to.path === "/parking-history") {
			console.log(`[PARKING HISTORY DEBUG] 접근 시도:`, {
				isAdmin: isAdmin,
				user_is_staff: userStore.me?.is_staff,
				will_be_blocked: isAdmin,
			});
		}

		if (isAdmin) {
			console.log(`[ROUTER GUARD] 관리자가 ${to.path} 접근 시도`);

			// 관리자 허용 페이지 목록 (화이트리스트)
			const adminAllowedPages = ["/admin-main", "/admin-parkinglogs", "/admin-plate-ocr", "/admin-login", "/modal-test", "/admin-error-test", "/holo"];

			// 관리자가 접근하면 안 되는 페이지 목록 (블랙리스트)
			const adminBlockedPages = ["/social-login-info", "/main", "/user-profile", "/parking-recommend", "/parking-complete"];

			// 관리자가 접근하면 안 되는 페이지인지 먼저 확인
			if (adminBlockedPages.includes(to.path)) {
				console.log(`[ROUTER GUARD] 관리자 차단 페이지 접근 시도: ${to.path} -> /admin-main 리다이렉트`);
				return next("/admin-main");
			}

			// 관리자 페이지이거나 허용된 테스트 페이지인 경우
			if (to.path.startsWith("/admin") || adminAllowedPages.includes(to.path)) {
				console.log(`[ROUTER GUARD] 관리자 허용 페이지 접근: ${to.path}`);
				return next();
			} else {
				// 관리자가 허용되지 않은 모든 페이지에 접근하려는 경우 차단
				console.log(`[ROUTER GUARD] 관리자 차단 페이지 접근 시도: ${to.path} -> /admin-main 리다이렉트`);
				return next("/admin-main");
			}
		}
	}

	// — 관리자 페이지 접근 시 로그인 체크
	if (to.path.startsWith("/admin") && to.path !== "/admin-login" && !isLoggedIn) {
		console.log("관리자 인증 필요, admin-login으로 이동");
		return next("/admin-login");
	}

	// 인증이 필요한 페이지인지 확인
	if (to.meta.requiresAuth) {
		if (!isLoggedIn) {
			// 로그인되지 않은 경우 로그인 페이지로 리다이렉트
			console.log("로그인이 필요한 페이지입니다. 로그인 페이지로 이동합니다.");
			next("/login");
		} else {
			// 추가 토큰 검증 (모바일 환경 안정성 개선)
			const token = SecureTokenManager.getSecureToken("access_token");
			if (!token) {
				console.warn("[ROUTER GUARD] 인증된 것으로 간주되었지만 토큰이 없음 - 로그인 페이지로 리다이렉트");
				next("/login");
				return;
			}
			// 비밀번호 인증이 필요한 페이지 체크 (user-setting)
			if (to.meta.requiresPasswordAuth) {
				console.log(`[ROUTER GUARD] 비밀번호 인증이 필요한 페이지 접근: ${to.path}`);

				const userStore = useUserStore();
				// 이메일 정보는 비밀번호 인증에서 동적으로 로딩됨

				// 소셜 로그인 유저 여부 확인
				const isSocialUser = userStore.me?.is_social_user || false;
				if (isSocialUser) {
					console.log("[ROUTER GUARD] 소셜 로그인 유저는 user-setting 접근 불가");
					alert("소셜 로그인 사용자는 이 페이지에 접근할 수 없습니다.");
					return next("/user-profile");
				}

				// 일회용 인증 토큰 확인
				const oneTimeAuth = sessionStorage.getItem("user-setting-one-time-auth");
				if (!oneTimeAuth) {
					console.log("[ROUTER GUARD] 일회용 인증 토큰 없음");
					alert("비밀번호 인증이 필요합니다. 프로필 페이지의 설정 아이콘을 눌러주세요.");
					return next("/user-profile");
				}

				try {
					const authData = JSON.parse(oneTimeAuth);
					const currentTime = Date.now();

					// 일회용 토큰 유효시간: 5초 (5,000ms)
					if (currentTime - authData.timestamp > 5000) {
						console.log("[ROUTER GUARD] 일회용 인증 토큰 만료");
						sessionStorage.removeItem("user-setting-one-time-auth");
						alert("인증 시간이 만료되었습니다. 다시 인증해주세요.");
						return next("/user-profile");
					}

					// 인증 토큰 확인 후 즉시 삭제 (일회용)
					sessionStorage.removeItem("user-setting-one-time-auth");
					console.log("[ROUTER GUARD] 일회용 인증 토큰 검증 완료 및 삭제");
				} catch (error) {
					console.log("[ROUTER GUARD] 일회용 인증 토큰 손상");
					sessionStorage.removeItem("user-setting-one-time-auth");
					alert("인증 정보가 올바르지 않습니다.");
					return next("/user-profile");
				}
			}

			// 일반 사용자 로직 (관리자 체크는 이미 위에서 완료)
			// 일반 사용자인 경우 차량 등록 여부 확인
			console.log("일반 사용자입니다. 차량 등록 여부를 확인합니다.");

			// 주차 히스토리 페이지 접근 시 추가 디버깅
			if (to.path === "/parking-history") {
				console.log(`[PARKING HISTORY DEBUG] 일반 사용자가 접근 중`);
			}
			
			// 차량 등록 확인 전 토큰 재검증 (모바일 환경 안정성)
			const vehicleCheckToken = SecureTokenManager.getSecureToken("access_token");
			if (!vehicleCheckToken) {
				console.warn("[ROUTER GUARD] 차량 등록 확인 중 토큰 소실 감지 - 로그인 페이지로 리다이렉트");
				next("/login");
				return;
			}
			
			const hasVehicle = await hasVehicleRegistered();
			console.log(`[ROUTER DEBUG] 차량 등록 여부: ${hasVehicle}`);

			if (!hasVehicle && to.name !== "social-login-info") {
				// 차량 등록이 안 되어 있고 social-login-info 페이지가 아닌 경우
				console.log("차량 등록이 필요합니다. 차량 등록 페이지로 이동합니다.");
				next("/social-login-info");
			} else if (hasVehicle && to.name === "social-login-info") {
				// 차량 등록이 되어 있는데 social-login-info 페이지에 접근하려는 경우
				console.log("이미 차량이 등록되어 있습니다. 메인 페이지로 이동합니다.");
				next("/main");
			} else {
				// 차량 등록이 되어 있거나 social-login-info 페이지인 경우 계속 진행
				next();
			}
		}
	} else {
		// 이미 로그인된 사용자가 로그인 관련 페이지에 접근하려는 경우
		if (isLoggedIn && (to.name === "login" || to.name === "signup" || to.name === "entry-page")) {
			// 관리자인지 확인하여 적절한 페이지로 리다이렉트
			const userStore = useUserStore();
			const isAdmin = userStore.me?.is_staff ?? false;

			if (isAdmin) {
				console.log("이미 로그인된 관리자입니다. 관리자 메인 페이지로 이동합니다.");
				next("/admin-main");
			} else {
				console.log("이미 로그인된 일반 사용자입니다. 차량 등록 여부를 확인합니다.");
				
				// 일반 사용자의 경우 차량 등록 여부에 따라 리다이렉트
				const hasVehicle = await hasVehicleRegistered();
				console.log(`[LOGIN REDIRECT] 차량 등록 여부: ${hasVehicle}`);
				
				if (hasVehicle) {
					console.log("차량 등록 완료. 메인 페이지로 이동합니다.");
					next("/main");
				} else {
					console.log("차량 등록 필요. 차량 등록 페이지로 이동합니다.");
					next("/social-login-info");
				}
			}
		} else {
			// 로그인되지 않은 사용자가 로그인 관련 페이지에 접근하는 경우 - 정상 허용
			if (!isLoggedIn && (to.name === "login" || to.name === "signup" || to.name === "entry-page")) {
				console.log(`[ROUTER GUARD] 비로그인 사용자의 ${to.path} 정상 접근`);
				next();
			}
			// 인증이 필요하지 않은 페이지도 관리자 접근 제어 적용
			else if (isLoggedIn) {
				const userStore = useUserStore();
				const isAdmin = userStore.me?.is_staff ?? false;

				if (isAdmin) {
					console.log(`[ADMIN ACCESS - 비인증페이지] 관리자가 ${to.path} 접근 시도`);

					// 관리자 허용 페이지 목록 (화이트리스트)
					const adminAllowedPages = ["/admin-main", "/admin-parkinglogs", "/admin-plate-ocr", "/modal-test", "/admin-error-test", "/holo"];

					// 관리자가 접근하면 안 되는 페이지 목록 (블랙리스트)
					const adminBlockedPages = ["/social-login-info", "/main", "/user-profile", "/parking-recommend", "/parking-complete"];

					// 관리자가 접근하면 안 되는 페이지인지 먼저 확인
					if (adminBlockedPages.includes(to.path)) {
						console.log(`[ADMIN ACCESS - 비인증페이지] 관리자 차단 페이지 접근 시도: ${to.path} -> /admin-main 리다이렉트`);
						return next("/admin-main");
					}

					// 관리자 페이지이거나 허용된 테스트 페이지인 경우
					if (to.path.startsWith("/admin") || adminAllowedPages.includes(to.path)) {
						console.log(`[ADMIN ACCESS - 비인증페이지] 허용된 페이지 접근: ${to.path}`);
						next();
					} else {
						// 관리자가 허용되지 않은 모든 페이지에 접근하려는 경우 차단
						console.log(`[ADMIN ACCESS - 비인증페이지] 차단된 페이지 접근 시도: ${to.path} -> /admin-main 리다이렉트`);
						next("/admin-main");
					}
				} else {
					// 일반 사용자는 그대로 진행
					next();
				}
			} else {
				// 로그인하지 않은 사용자는 그대로 진행
				console.log(`[ROUTER GUARD] 비로그인 사용자의 ${to.path} 접근 허용`);
				next();
			}
		}
	}
});

export default router;
