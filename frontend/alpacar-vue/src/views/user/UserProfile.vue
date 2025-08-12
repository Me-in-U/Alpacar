<template>
	<div class="user-profile">
		<!-- Header -->
		<Header />

		<!-- Content -->
		<div class="user-profile__content">
			<!-- 내 정보 카드 -->
			<div class="user-info">
				<div class="user-info__header">
					<!-- 좌측 스페이서(타이틀 중앙정렬 유지용) -->
					<div class="user-info__spacer"></div>

					<!-- 중앙: 닉네임 + 이메일(두 줄) -->
					<div class="user-info__headline">
						<div class="headline-name">
							{{ userInfo?.nickname || "-" }}
						</div>
						<div class="headline-email">
							{{ userInfo?.email || "-" }}
						</div>
					</div>

					<!-- 우측 설정 아이콘: 비밀번호 확인 모달 (소셜 로그인 유저는 숨김) -->
					<img 
						v-if="!isSocialUser"
						class="settings-icon" 
						src="@/assets/setting.png" 
						alt="설정" 
						@click="openSettingsAuthModal" 
					/>
				</div>

				<!-- ▼ 더보기 영역 -->
				<transition name="fade">
					<div v-if="isInfoExpanded">
						<!-- 이름 -->
						<div class="user-info__item">
							<div class="user-info__icon-wrapper">
								<div class="user-info__icon user-info__icon--name"></div>
							</div>
							<div class="user-info__content">
								<div class="user-info__label">이름</div>
								<div class="user-info__value">{{ userInfo?.name || "-" }}</div>
							</div>
						</div>

						<div class="user-info__divider"></div>

						<!-- 이메일 -->
						<div class="user-info__item">
							<div class="user-info__icon-wrapper">
								<div class="user-info__icon user-info__icon--email"></div>
							</div>
							<div class="user-info__content">
								<div class="user-info__label">이메일</div>
								<div class="user-info__value">{{ userInfo?.email || "-" }}</div>
							</div>
						</div>

						<div class="user-info__divider"></div>

						<!-- 닉네임(별도 아이콘) -->
						<div class="user-info__item">
							<div class="user-info__icon-wrapper">
								<div class="user-info__icon user-info__icon--nickname"></div>
							</div>
							<div class="user-info__content">
								<div class="user-info__label">닉네임</div>
								<div class="user-info__value">{{ userInfo?.nickname || "-" }}</div>
							</div>
						</div>

						<div class="user-info__divider"></div>

						<!-- 전화번호 -->
						<div class="user-info__item">
							<div class="user-info__icon-wrapper">
								<div class="user-info__icon user-info__icon--phone"></div>
							</div>
							<div class="user-info__content">
								<div class="user-info__label">전화번호</div>
								<div class="user-info__value">{{ formatPhoneNumber(userInfo?.phone) || "-" }}</div>
							</div>
						</div>
					</div>
				</transition>

				<!-- 화살표 토글 버튼 -->
				<button class="expand-toggle" :class="{ 'is-open': isInfoExpanded }" @click="isInfoExpanded = !isInfoExpanded" aria-label="자세히 보기">
					<svg viewBox="0 0 24 24" aria-hidden="true">
						<path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z" fill="currentColor" />
					</svg>
				</button>
			</div>

			<!-- 내 차량정보 -->
			<div class="section-header">
				<div class="section-title">내 차량정보</div>
				<div class="button button--secondary" @click="showVehicleModal = true">
					<div class="button__text">내 차 추가</div>
				</div>
			</div>

			<div class="vehicle-list">
				<div v-for="vehicle in displayedVehicles" :key="vehicle.id" class="vehicle-card">
					<img :src="getVehicleImageUrl(vehicle.model?.image_url)" alt="차량 이미지" class="vehicle-card__image" @error="(e) => (e.target as HTMLImageElement).src = defaultCarImage" />
					<div class="vehicle-card__info">
						<div><strong>번호판:</strong> {{ vehicle.license_plate }}</div>
						<div><strong>모델:</strong> {{ vehicle.model?.brand || "알파카" }} {{ vehicle.model?.model_name || "차량" }}</div>
					</div>
					<div class="vehicle-card__actions">
						<div class="vehicle-card__delete" @click="removeVehicle(vehicle.id)">삭제</div>
					</div>
				</div>
			</div>

			<div class="button-container" v-if="vehicles.length > 3">
				<div class="button button--more" @click="showAllVehicles = !showAllVehicles">
					<div class="button__text">
						{{ showAllVehicles ? "접기" : `더보기 (${vehicles.length - 3})` }}
					</div>
				</div>
			</div>

			<!-- 최하단 로그아웃 -->
			<div class="logout-container" @click="handleLogout">로그아웃</div>
		</div>

		<!-- Bottom Navigation -->
		<BottomNavigation />

		<!-- 차량 추가 모달 -->
		<div v-if="showVehicleModal" class="modal-overlay" @click="showVehicleModal = false">
			<div class="modal modal--vehicle" @click.stop>
				<h3 class="modal__title">차량 번호를 입력하세요</h3>

				<div class="modal__input-field">
					<input v-model="vehicleNumber" type="text" placeholder="예: 12가3456" class="modal__input" @input="handleVehicleNumberInput" maxlength="8" />
				</div>

				<!-- 중복체크 버튼 제거: 실시간 상태 표시 -->
				<div class="license-status" v-if="vehicleNumber">
					<span v-if="plateStatus === 'checking'" class="status checking">확인 중...</span>
					<span v-else-if="plateStatus === 'ok'" class="status ok">✔ 사용 가능</span>
					<span v-else-if="plateStatus === 'duplicate'" class="status duplicate">✗ 이미 등록된 차량</span>
					<span v-else-if="plateStatus === 'error'" class="status error">검증 실패, 다시 시도</span>
					<span v-else-if="!isVehicleNumberValid" class="status error">올바른 차량번호 형식으로 입력해주세요</span>
				</div>

				<button class="modal__button" @click="addVehicle" :disabled="!canAddVehicle">등록완료</button>
			</div>
		</div>

		<!-- 차량 1대 경고 모달 -->
		<div v-if="showSingleVehicleWarning" class="modal-overlay" @click="showSingleVehicleWarning = false">
			<div class="modal modal--warning" @click.stop>
				<h3 class="modal__title">차량이 1대밖에 없어 삭제할 수 없습니다.</h3>
				<button class="modal__button" @click="showSingleVehicleWarning = false">확인</button>
			</div>
		</div>

		<!-- 설정 진입 전 비밀번호 인증 모달 -->
		<div v-if="showSettingsAuthModal" class="modal-overlay" @click="closeSettingsAuthModal">
			<div class="modal modal--password-auth" @click.stop>
				<h3 class="modal__title">비밀번호 확인</h3>

				<div class="modal__input-field">
					<input v-model="settingsPassword" type="password" placeholder="현재 비밀번호를 입력하세요" class="modal__input" @keyup.enter="verifySettingsPassword" maxlength="20" />
				</div>

				<div v-if="settingsAuthError" class="error-message" style="margin-top: -10px; margin-bottom: 20px">
					{{ settingsAuthError }}
				</div>

				<div class="modal__buttons">
					<button class="modal__button modal__button--left" @click="verifySettingsPassword" :disabled="!settingsPassword || settingsAuthLoading">
						{{ settingsAuthLoading ? "확인 중..." : "확인" }}
					</button>
					<button class="modal__button modal__button--right" @click="closeSettingsAuthModal" :disabled="settingsAuthLoading">취소</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";
import defaultCarImage from "@/assets/alpaka_in_car.png";

import { ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { BACKEND_BASE_URL } from "@/utils/api";

const router = useRouter();
const userStore = useUserStore();

/* 상태 / 계산 */
const userInfo = computed(() => userStore.me);
const vehicles = computed(() => userStore.vehicles);

// 소셜 로그인 유저 여부 확인
const isSocialUser = computed(() => {
	// 소셜 로그인 유저는 Google OAuth를 통해 가입한 경우
	// 이메일이 Google 이메일이거나 별도 플래그가 있을 수 있음
	const email = userInfo.value?.email;
	if (!email) return false;
	
	// Google OAuth 사용자는 보통 소셜 로그인 정보를 별도로 저장
	// 여기서는 간단히 구글 이메일로 판단
	return email.includes('gmail.com');
});

const showAllVehicles = ref(false);
const displayedVehicles = computed(() => (vehicles.value.length <= 3 ? vehicles.value : showAllVehicles.value ? vehicles.value : vehicles.value.slice(0, 3)));

/* 사용자 정보 카드 토글 */
const isInfoExpanded = ref(false);

/* 차량 추가/삭제 */
const vehicleNumber = ref("");
const plateRegex = /^(?:0[1-9]|[1-9]\d|[1-9]\d{2})[가-힣][1-9]\d{3}$/;
const isVehicleNumberValid = computed(() => plateRegex.test(vehicleNumber.value));

// 실시간 중복 상태: idle | checking | ok | duplicate | error
const plateStatus = ref<"idle" | "checking" | "ok" | "duplicate" | "error">("idle");
let plateTimer: ReturnType<typeof setTimeout> | null = null;

const canAddVehicle = computed(() => isVehicleNumberValid.value && plateStatus.value === "ok");

const showVehicleModal = ref(false);
const showSingleVehicleWarning = ref(false);

const handleVehicleNumberInput = (e: Event) => {
	const target = e.target as HTMLInputElement;
	const cleanValue = target.value.replace(/[^0-9ㄱ-ㅎㅏ-ㅣ가-힣]/g, "").slice(0, 8);
	vehicleNumber.value = cleanValue;
	plateStatus.value = "idle";
};
// 마운트 시 내 차량 목록 로드
onMounted(async () => {
	try {
		await userStore.fetchMyVehicles(); // Pinia 액션 가정
	} catch (e) {
		console.error("[fetchMyVehicles] failed:", e);
	}
});
// 디바운스 중복 검증
watch(vehicleNumber, () => {
	if (plateTimer) clearTimeout(plateTimer);
	if (!vehicleNumber.value) {
		plateStatus.value = "idle";
		return;
	}
	if (!isVehicleNumberValid.value) {
		plateStatus.value = "idle";
		return;
	}
	plateStatus.value = "checking";
	plateTimer = setTimeout(async () => {
		try {
			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/check-license/?license=${encodeURIComponent(vehicleNumber.value)}`);
			if (!res.ok) throw new Error();
			const data = await res.json();
			plateStatus.value = data.exists ? "duplicate" : "ok";
		} catch {
			plateStatus.value = "error";
		}
	}, 400);
});

// 차량 등록 (중복이면 서버 에러 메시지 사용)
const addVehicle = async () => {
	if (!canAddVehicle.value) {
		alert("차량번호를 확인해주세요.");
		return;
	}
	const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
	if (!token) {
		alert("로그인이 필요합니다.");
		router.push("/login");
		return;
	}
	try {
		const response = await fetch(`${BACKEND_BASE_URL}/user/vehicle/`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${token}`,
			},
			body: JSON.stringify({
				license_plate: vehicleNumber.value.trim(),
			}),
		});

		if (response.ok) {
			alert("차량이 성공적으로 등록되었습니다!");
			showVehicleModal.value = false;
			vehicleNumber.value = "";
			plateStatus.value = "idle";
			try {
				// await userStore.fetchMyVehicles();
			} catch {}
		} else {
			const contentType = response.headers.get("content-type");
			if (contentType && contentType.includes("application/json")) {
				const err = await response.json();
				alert("차량 등록 실패: " + (err.detail || err.message || "서버 오류"));
				if ((err.detail || "").includes("이미") || response.status === 400) {
					plateStatus.value = "duplicate";
				}
			} else {
				if (response.status === 401) {
					alert("인증이 만료되었습니다. 다시 로그인해주세요.");
					router.push("/login");
				} else if (response.status === 404) {
					alert("API 엔드포인트를 찾을 수 없습니다.");
				} else {
					alert("차량 등록 실패 (코드: " + response.status + ")");
				}
			}
		}
	} catch (e) {
		console.error(e);
		alert("차량 등록 중 오류가 발생했습니다.");
		plateStatus.value = "error";
	}
};

const removeVehicle = async (id: number) => {
	if (vehicles.value.length <= 1) {
		showSingleVehicleWarning.value = true;
		return;
	}
	if (!confirm("차량을 정말 삭제하시겠습니까?")) return;
	try {
		await userStore.removeVehicle(id); // 서버 의존. 필요시 주석
		alert("차량이 삭제되었습니다. (테스트)");
	} catch (e) {
		console.error(e);
		alert("차량 삭제 중 오류가 발생했습니다. (테스트 모드)");
	}
};

/* 기타 */
const formatPhoneNumber = (phone: string | undefined | null) => {
	if (!phone) return null;
	const digits = phone.replace(/\D/g, "");
	if (digits.length !== 11) return phone;
	return digits.replace(/(\d{3})(\d{4})(\d{4})/, "$1-$2-$3");
};

const getVehicleImageUrl = (imageUrl: string | undefined) => {
	if (!imageUrl) return defaultCarImage;
	if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) return imageUrl;
	const cleanImageUrl = imageUrl.startsWith("/") ? imageUrl : `/${imageUrl}`;
	const backendUrl = BACKEND_BASE_URL.replace(/\/api$/, "");
	return `${backendUrl}${cleanImageUrl}`;
};

const handleLogout = () => {
	// 사용자 스토어 클리어
	userStore.clearUser();
	
	// 로컬 스토리지에서 인증 관련 데이터 모두 삭제
	[
		"access_token", "refresh_token",
		"access", "refresh", "accessToken", "refreshToken",
		"token", "user"
	].forEach((key) => localStorage.removeItem(key));
	
	// 세션 스토리지에서도 제거
	[
		"access_token", "refresh_token",
		"access", "refresh", "accessToken", "refreshToken",
		"token", "user"
	].forEach((key) => sessionStorage.removeItem(key));
	
	// 로그인 페이지로 리다이렉트
	router.push("/login");
};

/* ===== 설정 진입 전 비밀번호 인증 (UserSetting의 currentPassword 컨셉 재사용) ===== */
const showSettingsAuthModal = ref(false);
const settingsPassword = ref("");
const settingsAuthError = ref("");
const settingsAuthLoading = ref(false);

const openSettingsAuthModal = () => {
	settingsPassword.value = "";
	settingsAuthError.value = "";
	showSettingsAuthModal.value = true;
};

const closeSettingsAuthModal = () => {
	showSettingsAuthModal.value = false;
	settingsPassword.value = "";
	settingsAuthError.value = "";
};

const verifySettingsPassword = async () => {
	settingsAuthError.value = "";

	if (!settingsPassword.value) {
		settingsAuthError.value = "비밀번호를 입력하세요.";
		return;
	}

	const email = userInfo.value?.email;
	if (!email) {
		settingsAuthError.value = "사용자 이메일 정보를 찾을 수 없습니다. 다시 로그인해주세요.";
		return;
	}

	settingsAuthLoading.value = true;
	try {
		// 현재 이메일 + 입력 비밀번호로 로그인 엔드포인트를 호출해 검증만 수행
		const res = await fetch(`${BACKEND_BASE_URL}/auth/login/`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Accept: "application/json",
			},
			body: JSON.stringify({ email, password: settingsPassword.value }),
		});

		if (!res.ok) {
			// 서버가 주는 메시지 최대한 노출
			let msg = "비밀번호가 일치하지 않습니다.";
			try {
				const err = await res.json();
				msg = err.detail || err.message || msg;
			} catch {}
			settingsAuthError.value = msg;
			return;
		}

		// 성공: 토큰은 저장/갱신하지 않고 바로 폐기(검증 목적)
		closeSettingsAuthModal();
		
		// 일회용 인증 토큰 생성 (5초간만 유효)
		const oneTimeToken = {
			timestamp: Date.now(),
			userEmail: email,
			token: `auth_${Date.now()}_${Math.random()}`
		};
		sessionStorage.setItem('user-setting-one-time-auth', JSON.stringify(oneTimeToken));
		
		router.push("/user-setting");
	} catch (e) {
		console.error(e);
		settingsAuthError.value = "네트워크 오류로 인증할 수 없습니다.";
	} finally {
		settingsAuthLoading.value = false;
	}
};
</script>

<style scoped>
.user-profile {
	width: 440px;
	height: 956px;
	position: relative;
	background: #f3edea;
	overflow: hidden;
	margin: 0 auto;
}

.user-profile__content {
	position: relative;
	padding-top: 80px;
	height: calc(100% - 160px);
	overflow-y: auto;
	padding-left: 20px;
	padding-right: 20px;
}

/* ── User Info Card ── */
.user-info {
	background: #ffffff;
	border-radius: 16px;
	overflow: hidden;
	margin-bottom: 30px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
	border: 1px solid rgba(119, 107, 93, 0.1);
	position: relative;
}

.user-info::before {
	content: "";
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 3px;
	background: linear-gradient(90deg, #776b5d, #8b7d6b, #776b5d);
	border-radius: 16px 16px 0 0;
}

.user-info__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 14px 12px 12px 12px;
	background: linear-gradient(135deg, #f8f7f5 0%, #f5f4f2 100%);
	border-bottom: 1px solid rgba(119, 107, 93, 0.08);
}

.user-info__spacer {
	width: 24px;
	height: 24px;
	flex: 0 0 24px;
}

/* 헤더 안 닉네임/이메일 두 줄 */
.user-info__headline {
	flex: 1 1 auto;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.headline-name {
	font-size: 20px;
	font-weight: 800;
	color: #333333;
	line-height: 1.2;
}

.headline-email {
	font-size: 14px;
	color: #666666;
	line-height: 1.2;
	margin-top: 2px;
}

.settings-icon {
	width: 24px;
	height: 24px;
	cursor: pointer;
	flex: 0 0 24px;
}

/* ▼ 화살표 토글 버튼 */
.expand-toggle {
	appearance: none;
	background: transparent;
	border: none;
	margin-left: auto;
	padding: 8px 12px 12px 12px;
	cursor: pointer;
	color: #6b6257;
	display: flex;
	align-items: center;
	justify-content: center;
}
.expand-toggle svg {
	width: 22px;
	height: 22px;
	transition: transform 0.18s ease;
}
.expand-toggle.is-open svg {
	transform: rotate(180deg);
}

/* ── User Info Rows (펼쳐질 내용) ── */
.user-info__item {
	display: flex;
	align-items: center;
	padding: 18px 20px;
	min-height: 64px;
	transition: background-color 0.2s ease;
}
.user-info__item:hover {
	background-color: rgba(119, 107, 93, 0.02);
}

.user-info__icon-wrapper {
	margin-right: 16px;
	flex-shrink: 0;
}

.user-info__icon {
	width: 40px;
	height: 40px;
	border-radius: 10px;
	position: relative;
	transition: transform 0.2s ease;
}
.user-info__icon::before {
	content: "";
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	width: 20px;
	height: 20px;
	background-repeat: no-repeat;
	background-position: center;
	background-size: contain;
}

/* 이메일 */
.user-info__icon--email {
	background: linear-gradient(135deg, #4285f4, #34a853);
}
.user-info__icon--email::before {
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 24 24'%3E%3Cpath d='M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.89 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z'/%3E%3C/svg%3E");
}

/* 이름 */
.user-info__icon--name {
	background: linear-gradient(135deg, #ff6b6b, #ff8e53);
}
.user-info__icon--name::before {
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 24 24'%3E%3Cpath d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E");
}

/* 닉네임(보라 그라데이션 + 별 배지) */
.user-info__icon--nickname {
	background: linear-gradient(135deg, #7c4dff, #536dfe);
}
.user-info__icon--nickname::before {
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cg fill='white'%3E%3Cpath d='M12 12a4 4 0 1 0-0.001-8.001A4 4 0 0 0 12 12z'/%3E%3Cpath d='M4 20c0-3.313 4.477-6 8-6s8 2.687 8 6v1H4v-1z'/%3E%3C/g%3E%3Cpath d='M18.5 3.8l.7 1.6 1.7.2-1.3 1.2.4 1.6-1.5-.8-1.5.8.4-1.6-1.3-1.2 1.7-.2.7-1.6z' fill='%23FFD54F'/%3E%3C/svg%3E");
}

/* 전화번호 */
.user-info__icon--phone {
	background: linear-gradient(135deg, #00bcd4, #2196f3);
}
.user-info__icon--phone::before {
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 24 24'%3E%3Cpath d='M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z'/%3E%3C/svg%3E");
}

.user-info__content {
	flex: 1;
	min-width: 0;
}

.user-info__label {
	font-size: 14px;
	font-weight: 500;
	color: #776b5d;
	margin-bottom: 2px;
}

.user-info__value {
	font-size: 16px;
	font-weight: 600;
	color: #333333;
	word-break: break-all;
}

.user-info__divider {
	height: 1px;
	background: linear-gradient(90deg, transparent, rgba(119, 107, 93, 0.1), transparent);
	margin: 0 20px 0 76px;
}

/* Section / Buttons */
.section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 10px;
}
.section-title {
	font-size: 20px;
	font-weight: 600;
	margin-bottom: 0;
}

.button {
	background: #776b5d;
	border-radius: 5px;
	cursor: pointer;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 20px;
	align-self: flex-end;
}
.button--secondary {
	width: auto;
	height: 31px;
	padding: 0 12px;
}
.button--more {
	padding: 8px 12px;
	align-self: flex-end;
}
.button__text {
	color: #fff;
	font-weight: 700;
	font-size: 13px;
}
.button-container {
	display: flex;
	justify-content: flex-end;
	width: 100%;
}

/* Vehicle / Modal / Logout */
.vehicle-list {
	margin-top: 10px;
}
.vehicle-card {
	display: flex;
	align-items: center;
	justify-content: space-between;
	height: 150px;
	background: #fff;
	border: 1px solid #ccc;
	border-radius: 10px;
	padding-right: 14px;
	margin-bottom: 15px;
}
.vehicle-card__image {
	width: 45%;
	height: 100%;
	object-fit: contain;
	border-radius: 5px;
	margin-right: 12px;
	background-color: transparent;
	flex-shrink: 0;
	padding: 2px;
}
.vehicle-card__info {
	font-size: 17px;
	white-space: normal;
	flex: 1;
	min-width: 0;
}
.vehicle-card__actions {
	display: flex;
	gap: 12px;
}
.vehicle-card__delete {
	font-size: 16px;
	cursor: pointer;
}

.logout-container {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 14px 0 24px 0;
	color: #000000;
	font-weight: 400;
	cursor: pointer;
	font-size: 12px;
	text-decoration: underline;
}

/* Modal */
.modal-overlay {
	position: fixed;
	inset: 0;
	background: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
}
.modal {
	background: #f3eeea;
	width: 90%;
	max-width: 320px;
	padding: 27px 24px 50px;
	border-radius: 0;
}
.modal__title {
	font-size: 18px;
	font-weight: 600;
	text-align: center;
	margin-bottom: 30px;
}
.modal__input-field {
	width: 100%;
	background: #fff;
	border: 1px solid #ccc;
	margin-bottom: 30px;
	padding: 10px 15px;
	box-sizing: border-box;
}
.modal__input {
	width: 100%;
	border: none;
	outline: none;
	font-size: 16px;
	padding: 0;
	box-sizing: border-box;
}
.modal__button {
	width: 100%;
	height: 50px;
	background: #776b5d;
	color: #fff;
	border: none;
	font-size: 16px;
	font-weight: 600;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
}
.modal__buttons {
	display: flex;
	justify-content: space-between;
	gap: 20px;
}
.modal__button--left,
.modal__button--right {
	width: 48%;
}

.license-check-section {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 15px;
}

.license-check-button {
	background: #776b5d;
	color: white;
	border: none;
	padding: 8px 12px;
	border-radius: 5px;
	cursor: pointer;
	font-size: 14px;
}

.license-check-button:disabled {
	background: #ccc;
	cursor: not-allowed;
}

.check-success {
	color: #4caf50;
	font-size: 14px;
	font-weight: 600;
}

.check-error {
	color: #f44336;
	font-size: 14px;
	font-weight: 600;
}

.error-message {
	color: #f44336;
	font-size: 14px;
	margin-bottom: 15px;
}

/* Fade 애니메이션 */
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}

/* 중복체크 버튼 제거 후 상태 표시 스타일 */
.license-status {
	margin-top: -10px;
	margin-bottom: 15px;
	min-height: 20px;
	display: flex;
	align-items: center;
	font-size: 14px;
	font-weight: 600;
	gap: 6px;
}
.status.ok {
	color: #4caf50;
}
.status.duplicate {
	color: #f44336;
}
.status.error {
	color: #ff9800;
}
.status.checking {
	color: #776b5d;
}

/* Responsive */
@media (max-width: 440px) {
	.user-profile {
		width: 100vw;
		height: 100vh;
	}
	.user-profile__content {
		padding-left: 15px;
		padding-right: 15px;
	}
	.headline-name {
		font-size: 18px;
	}
	.headline-email {
		font-size: 13px;
	}
	.user-info__item {
		padding: 14px 16px;
		min-height: 56px;
	}
	.user-info__icon {
		width: 36px;
		height: 36px;
	}
	.user-info__icon::before {
		width: 18px;
		height: 18px;
	}
	.user-info__label {
		font-size: 13px;
	}
	.user-info__value {
		font-size: 15px;
	}
	.user-info__divider {
		margin: 0 16px 0 64px;
	}
}

@media (min-width: 441px) {
	.user-profile {
		width: 440px;
		height: auto;
		min-height: 100vh;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
	}
	.user-profile__content {
		flex: 1;
		height: auto;
		min-height: calc(100vh - 160px);
		padding-bottom: 20px;
	}
}
</style>
