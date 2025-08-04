import { createRouter, createWebHistory } from "vue-router";
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
import AdminParkingReassign from "@/views/admin/AdminParkingReassign.vue";
import ParkingRecommend from "@/views/user/ParkingRecommend.vue";
import ParkingComplete from "@/views/user/ParkingComplete.vue";
import ParkingHistory from "@/views/user/ParkingHistory.vue";
import ModalTest from "@/views/user/ModalTest.vue";
import AdminErrorModalTest from "@/views/admin/AdminErrorModalTest.vue";
import SocialLoginCallback from "@/views/user/SocialLoginCallback.vue";
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
		},
		{
			path: "/main",
			name: "main",
			component: MainPage,
		},
		{
			path: "/parking-history",
			name: "parking-history",
			component: ParkingHistory,
		},
		{
			path: "/user-profile",
			name: "user-profile",
			component: UserProfile,
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
		},
		{
			path: "/admin-parkinglogs",
			name: "admin-parkinglogs",
			component: AdminParkingLogs,
		},
		{
			path: "/admin-parkingreassign",
			name: "admin-parkingreassign",
			component: AdminParkingReassign,
		},
		{
			path: "/parking-recommend",
			name: "parking-recommend",
			component: ParkingRecommend,
		},
		{
			path: "/parking-complete",
			name: "parking-complete",
			component: ParkingComplete,
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
			path: "/social-login-callback",
			name: "social-login-callback",
			component: SocialLoginCallback,
		},
	],
});

export default router;
