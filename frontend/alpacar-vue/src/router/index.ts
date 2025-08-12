import { createRouter, createWebHistory } from "vue-router";

// 라우터 메타 타입 정의
declare module "vue-router" {
	interface RouteMeta {
		requiresAuth?: boolean;
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
import AdminParkingReassign from "@/views/admin/AdminParkingReassign.vue";
import ParkingRecommend from "@/views/user/ParkingRecommend.vue";
import ParkingComplete from "@/views/user/ParkingComplete.vue";
import ParkingHistory from "@/views/user/ParkingHistory.vue";
import ModalTest from "@/views/user/ModalTest.vue";
import AdminErrorModalTest from "@/views/admin/AdminErrorModalTest.vue";
import NotificationTestView from "@/views/admin/NotificationTestView.vue";
import GoogleCallback from "@/views/user/GoogleCallback.vue";
import MainWithHolo from "@/views/user/MainWithHolo.vue";
import { BACKEND_BASE_URL } from "@/utils/api";
import { useUserStore } from "@/stores/user";
import UserSetting from "@/views/user/UserSetting.vue";

// 로그인 상태 확인 함수
function isAuthenticated(): boolean {
	const token = localStorage.getItem("access_token");
	if (!token) {
		return false;
	}

	// 토큰이 있으면 일단 인증된 것으로 간주
	// 실제 API 호출 시 토큰 유효성은 각 컴포넌트에서 처리
	return true;
}

// 차량 등록 여부 확인 함수
async function hasVehicleRegistered(): Promise<boolean> {
	const token = localStorage.getItem("access_token");
	if (!token) {
		return false;
	}

	try {
		const response = await fetch(`${BACKEND_BASE_URL}/vehicles/check/`, {
			method: "GET",
			headers: {
				Authorization: `Bearer ${token}`,
				"Content-Type": "application/json",
			},
		});

		if (response.ok) {
			const data = await response.json();
			return data.has_vehicle ?? false;
		}
		return false;
	} catch (error) {
		console.error("차량 등록 여부 확인 중 오류:", error);
		return false;
	}
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
			path: "/admin-parkingreassign",
			name: "admin-parkingreassign",
			component: AdminParkingReassign,
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
        {
            path: "/notification-test",
            name: "notification-test",
            component: NotificationTestView,
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
			path: "/user-setting", 
			name: "user-setting", 
			component: UserSetting
		},
	],
});

// 네비게이션 가드 추가
router.beforeEach(async (to, from, next) => {
	const isLoggedIn = isAuthenticated();
	
	console.log(`[ROUTER GUARD] 페이지 접근: ${to.path}, 로그인 상태: ${isLoggedIn}`);

	// **최우선 순위: 로그인된 사용자가 관리자인 경우 접근 제어**
	if (isLoggedIn) {
		const userStore = useUserStore();
		console.log(`[ROUTER GUARD] 사용자 스토어 상태:`, userStore.me);
		
		// 사용자 정보가 없으면 localStorage에서 확인 시도
		if (!userStore.me) {
			const storedUser = localStorage.getItem('user');
			if (storedUser) {
				try {
					const userData = JSON.parse(storedUser);
					console.log(`[ROUTER GUARD] localStorage에서 사용자 정보 복구:`, userData);
					userStore.setUser(userData);
				} catch (e) {
					console.error(`[ROUTER GUARD] localStorage 사용자 정보 파싱 실패:`, e);
				}
			}
		}
		
		const isAdmin = userStore.me?.is_staff ?? false;
		console.log(`[ROUTER GUARD] 관리자 여부: ${isAdmin}`);
		
		if (isAdmin) {
			console.log(`[ROUTER GUARD] 관리자가 ${to.path} 접근 시도`);
			
					// 관리자 허용 페이지 목록 (화이트리스트)
		const adminAllowedPages = [
			"/admin-main", "/admin-parkinglogs", "/admin-parkingreassign",
			"/admin-plate-ocr", "/admin-login", "/modal-test", "/admin-error-test", 
			"/holo", "/notification-test"
		];
		
		// 관리자가 접근하면 안 되는 페이지 목록 (블랙리스트)
		const adminBlockedPages = [
			"/social-login-info", "/main", "/parking-history", "/user-profile",
			"/parking-recommend", "/parking-complete"
		];
			
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
			// 일반 사용자 로직 (관리자 체크는 이미 위에서 완료)
			// 일반 사용자인 경우 차량 등록 여부 확인
			console.log("일반 사용자입니다. 차량 등록 여부를 확인합니다.");
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
				console.log("이미 로그인된 사용자입니다. 메인 페이지로 이동합니다.");
				next("/main");
			}
		} else {
			// 인증이 필요하지 않은 페이지도 관리자 접근 제어 적용
			if (isLoggedIn) {
				const userStore = useUserStore();
				const isAdmin = userStore.me?.is_staff ?? false;
				
				if (isAdmin) {
					console.log(`[ADMIN ACCESS - 비인증페이지] 관리자가 ${to.path} 접근 시도`);
					
					// 관리자 허용 페이지 목록 (화이트리스트)
					const adminAllowedPages = [
						"/admin-main",
						"/admin-parkinglogs", 
						"/admin-parkingreassign",
						"/admin-plate-ocr",
						"/modal-test",
						"/admin-error-test", 
						"/holo",
						"/notification-test"
					];
					
					// 관리자가 접근하면 안 되는 페이지 목록 (블랙리스트)
					const adminBlockedPages = [
						"/social-login-info", "/main", "/parking-history", "/user-profile",
						"/parking-recommend", "/parking-complete"
					];
					
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
				next();
			}
		}
	}
});

export default router;
