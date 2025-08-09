<template>
	<div class="nav-container" @mouseleave="isOpen = false">
		<!-- NAVBAR -->
		<div class="nav-wrapper">
			<div class="logo" @click="handleMenuClick('/admin-main')">
				<img class="logo-img" src="@/assets/alpaca-192.png" alt="Logo" />
			</div>

			<!-- 데스크탑 메뉴 -->
			<div class="menu desktop-only">
				<div class="menu-item" @click="handleMenuClick('/admin-main')">실시간 주차 현황</div>
				<div class="menu-item" @click="handleMenuClick('/admin-plate-ocr')">실시간 번호판 인식</div>
				<div class="menu-item" @click="handleMenuClick('/admin-parkinglogs')">로그 및 기록</div>
				<div class="menu-item" @click="handleMenuClick('/admin-parkingreassign')">주차 배정 정보 변경</div>
				<img v-if="isLoggedIn" class="signout" src="@/assets/signout.png" alt="로그아웃" title="로그아웃" @click="handleLogout" />
			</div>

			<!-- 모바일 햄버거 -->
			<div class="hamburger-group mobile-only" @mouseenter="isOpen = true">
				<div class="hamburger">☰</div>
			</div>
		</div>

		<!-- DROPDOWN (navbar 바로 아래에 오버레이) -->
		<div v-if="isOpen" class="dropdown-menu" @mouseenter="isOpen = true" @mouseleave="isOpen = false">
			<div class="menu-item" @click="handleMenuClick('/admin-main')">실시간 주차 현황</div>
			<div class="menu-item" @click="handleMenuClick('/admin-plate-ocr')">실시간 번호판 인식</div>
			<div class="menu-item" @click="handleMenuClick('/admin-parkinglogs')">로그 및 기록</div>
			<div class="menu-item" @click="handleMenuClick('/admin-parkingreassign')">주차 배정 정보 변경</div>
			<img v-if="isLoggedIn" class="signout" src="@/assets/signout.png" alt="로그아웃" title="로그아웃" @click="handleLogout" />
		</div>

		<!-- 관리자 인증 필요 모달 -->
		<AdminAuthRequiredModal v-if="showAuthModal" @close="showAuthModal = false" />
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import AdminAuthRequiredModal from "@/views/admin/AdminAuthRequiredModal.vue";

const router = useRouter();
const route = useRoute();

const isOpen = ref(false);
const showAuthModal = ref(false);
const isLoggedIn = ref(false);

const emit = defineEmits<{ (e: "logout"): void }>();

function readAuth(): boolean {
  const token =
    localStorage.getItem("access_token") ||  // ← 스샷 기준 키
    localStorage.getItem("access") ||
    localStorage.getItem("accessToken") ||
    localStorage.getItem("adminAccess") ||
    localStorage.getItem("token");
  if (!token) return false;

  const raw = localStorage.getItem("user");
  if (!raw) return false;

  try {
    const user = JSON.parse(raw);
    return user?.is_staff === true; // ← 여기서 관리자 여부 체크
  } catch {
    return false;
  }
}

function refreshAuth() {
  isLoggedIn.value = readAuth();
}

onMounted(() => {
  refreshAuth();
  // 동일 탭에서는 storage 이벤트가 안 떠서, 다른 신호에도 갱신
  window.addEventListener("focus", refreshAuth);        // 탭 포커스 복귀
  window.addEventListener("visibilitychange", () => {   // 화면 전환
    if (!document.hidden) refreshAuth();
  });
});

// 라우트가 바뀔 때마다 재평가 (로그인 후 리다이렉트 시)
watch(() => route.fullPath, () => refreshAuth());

onUnmounted(() => {
  window.removeEventListener("focus", refreshAuth);
});

const goTo = (path: string) => {
	isOpen.value = false;
	router.push(path);
};

const handleMenuClick = (path: string) => {
	if (!isLoggedIn.value) {
		showAuthModal.value = true;
		return;
	}
	goTo(path);
};

const handleLogout = () => {
  // 실제 저장된 키 반영 (스크린샷 기준)
  [
    "access_token", "refresh_token",
    "access", "refresh", "accessToken", "refreshToken",
    "adminAccess", "adminRefresh", "token",
    "is_staff", "user",
  ].forEach((k) => localStorage.removeItem(k));

  refreshAuth(); // 즉시 갱신
  emit("logout");
  router.replace("/admin-login");
};
</script>

<style scoped>
/* 전체 컨테이너: navbar + dropdown */
.nav-container {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	overflow: visible; /* dropdown이 밖으로 나와도 보이게 */
	z-index: 1000;
	margin: 0;
	padding: 0;
}

/* NAVBAR */
.nav-wrapper {
	background-color: #776b5d;
	height: 64px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 16px;
	box-sizing: border-box;
	width: 100%;
}

.logo-img {
	height: 36px;
	cursor: pointer;
}

/* 데스크탑 전용 메뉴 */
.menu.desktop-only {
	display: flex;
	gap: 40px;
	align-items: center;
}

/* 공통 메뉴 아이템 */
.menu-item {
	color: white;
	font-size: 16px;
	cursor: pointer;
	padding: 8px 16px;
	border-radius: 4px;
	transition: background-color 0.2s;
}
.menu-item:hover {
	background-color: #5f554b;
}

.signout {
  height: 22px;
  width: 16px;
  cursor: pointer;
}

/* 모바일 전용 햄버거 */
.mobile-only {
	display: none;
}
.hamburger {
	font-size: 24px;
	color: white;
	cursor: pointer;
	user-select: none;
	padding: 8px;
}

/* DROPDOWN - navbar 바로 아래, 오버레이 */
.dropdown-menu {
	position: absolute;
	top: 64px; /* navbar 높이 */
	left: 0;
	right: 0;
	background-color: #776b5d;
	display: flex;
	flex-direction: column;
	gap: 8px;
	padding: 16px;
	box-sizing: border-box;
	max-height: 50vh;
	overflow-y: auto;
	overflow-x: hidden;
	box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

/* 반응형 */
@media screen and (max-width: 768px) {
	.menu.desktop-only {
		display: none;
	}
	.mobile-only {
		display: block;
	}
}

/* 기본 페이지 스크롤 방지 */
html,
body {
	margin: 0;
	padding: 0;
	overflow-x: hidden;
}
</style>
