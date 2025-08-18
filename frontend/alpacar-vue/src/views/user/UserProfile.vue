<template>
	<div class="user-profile">
		<!-- Header -->
		<Header />

		<!-- Content -->
		<div class="user-profile__content">
			<!-- 내 정보 카드 -->
			<div class="user-info" :class="{ 'is-compact': isInfoExpanded }">
				<div class="user-info__header">
					<!-- 좌측 스페이서(타이틀 중앙정렬 유지용) -->
					<div class="user-info__spacer"></div>

					<!-- 중앙: 닉네임 + (이메일 제거) + 토글 -->
					<div class="user-info__headline">
						<div class="headline-name">
							{{ userInfo?.nickname || "-" }}
						</div>

						<!-- ↓ 이메일 줄 삭제하고, 토글 배치 -->
						<button
							class="headline-expand"
							type="button"
							@click="isInfoExpanded = !isInfoExpanded"
							:aria-label="isInfoExpanded ? '기본 정보 닫기' : '기본 정보 보기'"
						>
							<span class="expand-label">
								{{ isInfoExpanded ? '기본 정보 닫기' : '기본 정보 보기' }}
							</span>
							<svg class="expand-icon" viewBox="0 0 24 24" aria-hidden="true"
									:class="{ 'is-open': isInfoExpanded }">
								<path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z" fill="currentColor" />
							</svg>
						</button>
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
						<!-- 닉네임(별도 아이콘) -->
						<div
							class="user-info__item user-info__item--action"
							@click="openNicknameModal"
							role="button"
							tabindex="0"
							@keydown.enter.prevent="openNicknameModal"
							@keydown.space.prevent="openNicknameModal"
						>
							<div class="user-info__icon-wrapper">
								<div class="user-info__icon user-info__icon--nickname"></div>
							</div>
							<div class="user-info__content">
								<div class="user-info__label">닉네임</div>
								<div class="user-info__value">{{ userInfo?.nickname || "-" }}</div>
							</div>
							<span class="chevron" aria-hidden="true">
								<svg viewBox="0 0 24 24">
									<path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
								</svg>
							</span>
						</div>
						<div class="user-info__divider"></div>

						<!-- 이름 -->
						<div class="user-info__item">
							<div class="user-info__icon-wrapper">
								<div class="user-info__icon user-info__icon--name"></div>
							</div>
							<div class="user-info__content">
								<div class="user-info__label">이름</div>
								<div class="user-info__value">{{ isLoadingUserInfo ? '로딩 중...' : (userInfo?.name || "-") }}</div>
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
								<div class="user-info__value">{{ isLoadingUserInfo ? '로딩 중...' : (userInfo?.email || "-") }}</div>
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
								<div class="user-info__value">{{ isLoadingUserInfo ? '로딩 중...' : (formatPhoneNumber(userInfo?.phone) || "-") }}</div>
							</div>
						</div>
					</div>
				</transition>

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

			<!-- 알림 설정 -->
			<div class="section-title">알림 설정</div>
			<div class="notification-settings">
				<div class="notification-item">
					<div class="notification-item__content">
						<div class="notification-item__label">푸시 알림</div>
						<div class="notification-item__desc">주차 입출차 및 중요 알림 수신</div>
					</div>
					<div class="notification-item__toggle">
						<button class="toggle-button" :class="{ 'toggle-button--active': isNotificationEnabled }" @click="toggleNotifications">
							{{ isNotificationEnabled ? '켜짐' : '꺼짐' }}
						</button>
					</div>
				</div>

				<div class="notification-item">
					<div class="notification-item__content">
						<div class="notification-item__label">앱 설치하기</div>
						<div class="notification-item__desc">앱처럼 사용하기</div>
					</div>
					<div class="notification-item__toggle">
						<button class="install-button" @click="installPWA" :disabled="!canInstallPWA">
							{{ canInstallPWA ? '설치' : '설치됨' }}
						</button>
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
				<!-- X Close Button -->
				<button class="modal-close-btn" @click="showVehicleModal = false" aria-label="닫기">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
				
				<h3 class="modal__title">차량 번호를 입력하세요</h3>

				<div class="modal__input-field">
					<input v-model="vehicleNumber" type="text" placeholder="예: 12가3456" class="modal__input" @input="handleVehicleNumberInput" maxlength="8" />
				</div>

				<!-- 중복체크 버튼 제거: 실시간 상태 표시 -->
				<div class="license-status" v-if="vehicleNumber">
					<span v-if="plateStatus === 'checking'" class="status checking">확인 중...</span>
					<span v-else-if="plateStatus === 'ok'" class="status ok">✔ 사용 가능</span>
					<span v-else-if="plateStatus === 'duplicate'" class="status duplicate">✗ 이미 등록된 차량번호입니다</span>
					<span v-else-if="plateStatus === 'invalid'" class="status invalid">✗ 등록된 차량번호가 아닙니다</span>
					<span v-else-if="plateStatus === 'error'" class="status error">검증 실패, 다시 시도</span>
					<span v-else-if="!isVehicleNumberValid" class="status error">올바른 차량번호 형식으로 입력해주세요 (예: 12가3456)</span>
				</div>

				<button class="modal__button" @click="addVehicle" :disabled="!canAddVehicle">등록완료</button>
			</div>
		</div>

		<!-- 차량 1대 경고 모달 -->
		<div v-if="showSingleVehicleWarning" class="modal-overlay" @click="showSingleVehicleWarning = false">
			<div class="modal modal--warning" @click.stop>
				<!-- X Close Button -->
				<button class="modal-close-btn" @click="showSingleVehicleWarning = false" aria-label="닫기">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
				
				<h3 class="modal__title">차량이 1대밖에 없어 삭제할 수 없습니다.</h3>
				<button class="modal__button" @click="showSingleVehicleWarning = false">확인</button>
			</div>
		</div>

		<!-- 닉네임 수정 모달 -->
		<div
			v-if="showNicknameModal"
			class="modal-overlay"
			@click="showNicknameModal = false"
		>
			<div
				class="modal modal--nickname"
				@click.stop
			>
				<!-- X Close Button -->
				<button class="modal-close-btn" @click="showNicknameModal = false" aria-label="닫기">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
				
				<h3 class="modal__title">
					수정할 닉네임을 입력하세요
				</h3>

				<div class="modal__input-field">
					<input
						v-model="newNickname"
						@input="handleNicknameInput"
						@beforeinput="preventNicknameLengthExceed"
						@compositionstart="onNicknameCompositionStart"
						@compositionupdate="onNicknameCompositionUpdate"
						@compositionend="onNicknameCompositionEnd"
						@keypress="preventInvalidNicknameChars"
						type="text"
						placeholder="예: 주차하는알파카"
						class="modal__input"
						maxlength="18"
					/>
				</div>

				<div
					v-if="newNickname && !isNicknameValid"
					class="error-message"
				>
					닉네임은 한글, 영문, 숫자만 사용 가능 (2-18자)
				</div>

				<button
					class="modal__button"
					@click="updateNickname"
					:disabled="!isNicknameValid"
				>
					설정 완료
				</button>
			</div>
		</div>

		<!-- 설정 진입 전 비밀번호 인증 모달 -->
		<div v-if="showSettingsAuthModal" class="modal-overlay" @click="closeSettingsAuthModal">
			<div class="modal modal--password-auth" @click.stop>
				<!-- X Close Button -->
				<button class="modal-close-btn" @click="closeSettingsAuthModal" aria-label="닫기">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
				
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
import { subscribeToPushNotifications, unsubscribeFromPushNotifications, getSubscriptionStatus, showLocalNotification } from "@/utils/pwa";
import { alert, alertSuccess, alertWarning, alertError } from "@/composables/useAlert";

const router = useRouter();
const userStore = useUserStore();

/* 상태 / 계산 */
// 동적으로 로딩되는 사용자 상세 정보 (민감정보 포함)
const detailedUserInfo = ref<any>(null);
const isLoadingUserInfo = ref(false);

// 로컬 스토리지의 기본 사용자 정보 + 동적으로 로딩된 민감정보
const userInfo = computed(() => detailedUserInfo.value || userStore.me);

// 민감한 사용자 정보 동적 로딩
const loadDetailedUserInfo = async () => {
  if (isLoadingUserInfo.value) return;
  
  try {
    isLoadingUserInfo.value = true;
    const userData = await userStore.fetchDetailedUserInfo();
    detailedUserInfo.value = userData;
    console.log('[UserProfile] 사용자 상세 정보 로딩 완료');
  } catch (error) {
    console.error('[UserProfile] 사용자 정보 로딩 실패:', error);
    // 로딩 실패 시 기본 정보 사용 (민감정보 없이)
  } finally {
    isLoadingUserInfo.value = false;
  }
};
const vehicles = computed(() => userStore.vehicles);

// 소셜 로그인 유저 여부 확인
const isSocialUser = computed(() => {
	// 백엔드에서 제공하는 is_social_user 필드 사용
	return userInfo.value?.is_social_user || false;
});

const showAllVehicles = ref(false);
const displayedVehicles = computed(() => (vehicles.value.length <= 3 ? vehicles.value : showAllVehicles.value ? vehicles.value : vehicles.value.slice(0, 3)));

/* 사용자 정보 카드 토글 */
const isInfoExpanded = ref(false);

/* 차량 추가/삭제 */
const vehicleNumber = ref("");

// 한국 번호판 정규식 패턴 (더 정확한 한글 문자 제한)
const KOREAN_PLATE_CHARS = "가나다라마거너더러머버서어저고노도로모보소오조구누두루무부수우주아바사자허하호배";
const plateRegex = new RegExp(
  `^(?:0[1-9]|[1-9]\\d|[1-9]\\d{2})` +  // 01-99 또는 100-999
  `[${KOREAN_PLATE_CHARS}]` +              // 한글 1자 (지정된 문자만)
  `[1-9]\\d{3}$`                          // 1000-9999
);

const isVehicleNumberValid = computed(() => plateRegex.test(vehicleNumber.value));

// 실시간 중복 상태: idle | checking | ok | duplicate | invalid | error
const plateStatus = ref<"idle" | "checking" | "ok" | "duplicate" | "invalid" | "error">("idle");
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
			const url = `${BACKEND_BASE_URL}/vehicles/check-license/?license=${encodeURIComponent(vehicleNumber.value)}`;
			console.log('[차량번호 검증] 요청 URL:', url);
			console.log('[차량번호 검증] 원본 번호:', vehicleNumber.value);
			console.log('[차량번호 검증] 인코딩된 번호:', encodeURIComponent(vehicleNumber.value));
			
			const res = await fetch(url);
			console.log('[차량번호 검증] 응답 상태:', res.status, res.statusText);
			
			if (!res.ok) {
				console.error('[차량번호 검증] HTTP 오류:', res.status, res.statusText);
				throw new Error(`HTTP ${res.status}: ${res.statusText}`);
			}
			
			const data = await res.json();
			console.log('[차량번호 검증] 응답 데이터:', data);
			
			// 새로운 API 응답 형식 처리
			if (data.status === "valid") {
				plateStatus.value = "ok";
			} else if (data.status === "duplicate") {
				plateStatus.value = "duplicate";
			} else if (data.status === "invalid") {
				plateStatus.value = "invalid";
			} else {
				console.warn('[차량번호 검증] 예상치 못한 status:', data.status);
				plateStatus.value = "error";
			}
		} catch (error) {
			console.error('[차량번호 검증] 에러:', error);
			plateStatus.value = "error";
		}
	}, 400);
});

// 차량 등록 (중복이면 서버 에러 메시지 사용)
const addVehicle = async () => {
	if (!canAddVehicle.value) {
		await alertWarning("차량번호를 확인해주세요.");
		return;
	}
	const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
	if (!token) {
		await alertWarning("로그인이 필요합니다.");
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
			await alertSuccess("차량이 성공적으로 등록되었습니다!");
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
				await alertError("차량 등록 실패: " + (err.detail || err.message || "서버 오류"));
				if ((err.detail || "").includes("이미") || response.status === 400) {
					plateStatus.value = "duplicate";
				}
			} else {
				if (response.status === 401) {
					await alertError("인증이 만료되었습니다. 다시 로그인해주세요.");
					router.push("/login");
				} else if (response.status === 404) {
					await alertError("API 엔드포인트를 찾을 수 없습니다.");
				} else {
					await alertError("차량 등록 실패 (코드: " + response.status + ")");
				}
			}
		}
	} catch (e) {
		console.error(e);
		await alertError("차량 등록 중 오류가 발생했습니다.");
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
		await alertSuccess("차량이 삭제되었습니다. (테스트)");
	} catch (e) {
		console.error(e);
		await alertError("차량 삭제 중 오류가 발생했습니다. (테스트 모드)");
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


/* ====== 닉네임 ====== */
const showNicknameModal = ref(false);
const newNickname = ref("");
const isNicknameComposing = ref(false);
const isNicknameValid = computed(() => {
	const noSpecialChars = /^[a-zA-Z가-힣0-9]+$/.test(newNickname.value);
	const lengthValid = newNickname.value.length >= 2 && newNickname.value.length <= 18;
	return noSpecialChars && lengthValid;
});

const openNicknameModal = () => { 
	newNickname.value = userInfo.value?.nickname || ""; 
	showNicknameModal.value = true; 
};

const onNicknameCompositionStart = () => { isNicknameComposing.value = true; };
const onNicknameCompositionUpdate = (e: CompositionEvent) => {
	const input = e.target as HTMLInputElement;
	if (input.value.length > 18) {
		const truncated = input.value.slice(0, 18);
		input.value = truncated;
		newNickname.value = truncated;
	}
};
const onNicknameCompositionEnd = (e: Event) => {
	isNicknameComposing.value = false;
	const input = e.target as HTMLInputElement;
	const cleaned = input.value.replace(/[^a-zA-Z가-힣0-9]/g, "").slice(0, 18);
	if (input.value !== cleaned) {
		newNickname.value = cleaned;
		setTimeout(() => { input.value = cleaned; }, 0);
	}
};
const handleNicknameInput = (e: Event) => {
	const input = e.target as HTMLInputElement;
	if (input.value.length > 18) {
		const truncated = input.value.slice(0, 18);
		newNickname.value = truncated;
		input.value = truncated;
		return;
	}
	if (isNicknameComposing.value) return;
	const cleaned = input.value.replace(/[^a-zA-Z가-힣0-9]/g, "").slice(0, 18);
	if (input.value !== cleaned) {
		newNickname.value = cleaned;
		setTimeout(() => { if (input.value !== cleaned) input.value = cleaned; }, 0);
	}
};
const preventNicknameLengthExceed = (e: Event) => {
	const input = e.target as HTMLInputElement;
	const ev = e as InputEvent;
	const len = input.value.length;
	if (ev.inputType && (ev.inputType.includes("insert") || ev.inputType.includes("replace") || ev.inputType === "insertText" || ev.inputType === "insertCompositionText")) {
		if (len >= 18) { e.preventDefault(); return; }
		const data = ev.data || "";
		if (len + data.length > 18) { e.preventDefault(); return; }
	}
};
const preventInvalidNicknameChars = (e: KeyboardEvent) => {
	if (isNicknameComposing.value) return;
	const char = e.key;
	const input = e.target as HTMLInputElement;
	if (["Backspace","Delete","ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Tab","Enter","Escape"].includes(char)) return;
	if (e.isComposing || char === "Process") return;
	if (input.value.length >= 18) { e.preventDefault(); return; }
	if (!/[a-zA-Z가-힣0-9]/.test(char)) e.preventDefault();
};

const updateNickname = async () => {
	const nick = newNickname.value.trim();
	if (!nick) return await alertWarning("닉네임을 입력해주세요.");
	try {
		await userStore.updateProfile({ nickname: nick }); // 서버 의존(테스트 시 주석 가능)
		await alertSuccess("닉네임이 변경되었습니다.");
		showNicknameModal.value = false;
		newNickname.value = "";
	} catch (err: any) {
		console.error(err);
		await alertError("변경 실패: " + err.message);
	}
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


/* ====== 알림(PWA) ====== */
// 헤더와 동기화를 위해 userStore의 push_on 상태를 사용
const isNotificationEnabled = computed<boolean>({
  get: () => userStore.me?.push_on ?? false,
  set: (value: boolean) => {
    // userStore의 togglePush 메서드를 사용하여 상태 변경
    userStore.togglePush(value);
  }
});

const canInstallPWA = ref(false);
let deferredPrompt: any = null;

const toggleNotifications = async () => {
  try {
    console.log("[UserProfile] 푸시 알림 토글 시작:", !isNotificationEnabled.value);
    
    // userStore의 togglePush 메서드를 사용하여 헤더와 동기화
    await userStore.togglePush(!isNotificationEnabled.value);
    
    // 성공 메시지 표시
    if (isNotificationEnabled.value) {
      await alertSuccess("푸시 알림이 활성화되었습니다.");
      setTimeout(() => {
        showLocalNotification({ type: "general", title: "🎉 알림 설정 완료", body: "이제 주차 알림을 받을 수 있습니다!" });
      }, 1000);
    } else {
      await alertSuccess("푸시 알림이 해제되었습니다.");
    }
  } catch (e) {
    console.error("[UserProfile] 알림 설정 변경 중 오류:", e);
    await alertError(`알림 설정 변경 중 오류가 발생했습니다: ${e instanceof Error ? e.message : '알 수 없는 오류'}`);
  }
};

const installPWA = async () => {
  if (deferredPrompt) {
    try {
      deferredPrompt.prompt();
      const choiceResult = await deferredPrompt.userChoice;
      if (choiceResult.outcome === "accepted") { canInstallPWA.value = false; }
      deferredPrompt = null;
    } catch (e) {
      console.error(e);
      await alertError("PWA 설치 중 오류가 발생했습니다.");
    }
  } else if (window.matchMedia("(display-mode: standalone)").matches) {
    await alert("이미 PWA로 설치되어 실행 중입니다.");
  } else {
    const ua = navigator.userAgent.toLowerCase();
    if (ua.includes("android")) await alert('Chrome 메뉴 → "홈 화면에 추가"를 선택하세요.');
    else if (ua.includes("iphone") || ua.includes("ipad")) await alert('Safari 공유 버튼 → "홈 화면에 추가"를 선택하세요.');
    else await alert('브라우저 메뉴에서 "앱 설치" 또는 "홈 화면에 추가"를 선택하세요.');
  }
};

const checkNotificationStatus = async () => {
  try {
    // PWA 설치 상태만 확인 (알림 상태는 userStore에서 관리)
    const isStandalone = window.matchMedia("(display-mode: standalone)").matches;
    const isInWebAppiOS = (window.navigator as any).standalone === true;
    const isInstalled = isStandalone || isInWebAppiOS;
    canInstallPWA.value = !isInstalled && (!!deferredPrompt || "serviceWorker" in navigator);
    
    console.log("[UserProfile] 알림 상태 확인:", {
      userStorePushOn: userStore.me?.push_on,
      computedIsEnabled: isNotificationEnabled.value,
      canInstallPWA: canInstallPWA.value
    });
  } catch (e) {
    console.error("[UserProfile] 알림 상태 확인 중 오류:", e);
  }
};

const setupPWAListeners = () => {
  window.addEventListener("beforeinstallprompt", (e) => {
    (e as Event).preventDefault?.();
    deferredPrompt = e;
    canInstallPWA.value = true;
  });
  window.addEventListener("appinstalled", () => {
    canInstallPWA.value = false;
    deferredPrompt = null;
  });
};

onMounted(async () => {
  setupPWAListeners();
  await checkNotificationStatus();
  
  // 민감한 사용자 정보 동적 로딩
  await loadDetailedUserInfo();
});
</script>

<style scoped>
.user-profile {
	width: 440px;
	height: 956px;
	position: relative;
	background: #F9F5EC;
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
	background: linear-gradient(90deg, #4B3D34, #594D44, #4B3D34);
	border-radius: 16px 16px 0 0;
}

.user-info__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 14px 12px 12px 12px;
	background: linear-gradient(135deg, #EDE6DF 0%, #E1D6CC 100%);
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
	text-align: left;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
}

/* 펼쳐졌을 때(compact) 항목 높이 축소 */
.user-info.is-compact .user-info__item {
  /* 상하 여백 ↓ */
  padding: 10px 16px;
  /* min-height가 행 높이를 잡고 있으니 낮추거나 제거 */
  min-height: 52px; /* 필요하면 48px까지 낮춰도 OK */
}

/* 아이콘이 너무 커서 행 높이를 밀면 살짝만 줄이기(선택) */
.user-info.is-compact .user-info__icon {
  height: 36px;
  width: 36px;
}
.user-info.is-compact .user-info__icon::before {
  height: 18px;
  width: 18px;
}

/* Divider 좌우 여백도 살짝 줄이기(선택) */
.user-info.is-compact .user-info__divider {
  margin: 0 16px 0 64px;
}

/* 라벨-값 사이 간격 미세 조정(선택) */
.user-info.is-compact .user-info__label {
  margin-bottom: 1px;
}

.headline-name {
	font-size: 20px;
	font-weight: 800;
	color: #333333;
	line-height: 1.2;
	margin: 0;
}

/* 닉네임 아래 토글(텍스트+아이콘) */
.headline-expand {
  margin-top: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;            /* 글자와 아이콘 간격 */
  background: transparent;
  border: 0;
  padding: 0;
  color: #6b6257;
  cursor: pointer;
  border-radius: 6px;
	align-self: flex-start;
  margin-left: 0;
}

.headline-expand:focus-visible {
  outline: 2px solid rgba(119,107,93,0.4);
  outline-offset: 2px;
}

.settings-icon {
	width: 24px;
	height: 24px;
	cursor: pointer;
	flex: 0 0 24px;
}

/* ▼ 화살표 토글 버튼 */
/* 새 래퍼: 우측 정렬, 라벨-버튼 나란히 */
.user-info__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 12px 12px 12px; /* 카드 하단 패딩 */
  gap: 2px;                 /* 라벨과 버튼 간격 */
  color: #6b6257;
}

/* 라벨 모양 */
.expand-label {
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  line-height: 1;
	margin: 0;
}

.expand-toggle {
	appearance: none;
	background: transparent;
	border: none;
	margin-left: 0;
	padding: 8px 8px 12px 4px;
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

.expand-icon {
  width: 20px;
  height: 20px;
  transition: transform 0.18s ease;
}
.expand-icon.is-open {
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
  background: transparent;
}
.user-info__icon::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;

  /* 아이콘 색상 */
  background-color: #212730;

  /* 마스크 공통 옵션 */
  -webkit-mask-repeat: no-repeat;
          mask-repeat: no-repeat;
  -webkit-mask-position: center;
          mask-position: center;
  -webkit-mask-size: contain;
          mask-size: contain;

  /* 혹시 남아있을 기존 배경이미지 무효화 */
  background-image: none !important;
}

/* 닉네임: 큰 별 아이콘으로 변경 */
.user-info__icon--nickname { 
  background: transparent; 
}
.user-info__icon--nickname::before {
  /* 아이콘 자체를 조금 더 키워서 눈에 띄게 */
  width: 22px;
  height: 22px;

  /* 단색 채우기 */
  background-color: #212730;

  /* 마스크(별) */
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M12 17.27L18.18 21 16.54 13.97 22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z'/%3E%3C/svg%3E");
          mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M12 17.27L18.18 21 16.54 13.97 22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z'/%3E%3C/svg%3E");
  -webkit-mask-repeat: no-repeat;
          mask-repeat: no-repeat;
  -webkit-mask-position: center;
          mask-position: center;
  -webkit-mask-size: contain;
          mask-size: contain;
}

/* 이름 */
.user-info__icon--name { background: transparent; }
.user-info__icon--name::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E");
          mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E");
}

/* 이메일 */
.user-info__icon--email { background: transparent; }
.user-info__icon--email::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.89 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z'/%3E%3C/svg%3E");
          mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.89 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z'/%3E%3C/svg%3E");
}

/* 전화번호 */
.user-info__icon--phone { background: transparent; }
.user-info__icon--phone::before {
  -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z'/%3E%3C/svg%3E");
          mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z'/%3E%3C/svg%3E");
}
.user-info__content {
	flex: 1;
	min-width: 0;
}

.user-info__label {
	font-size: 14px;
	font-weight: 500;
	color: #4B3D34;
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
	background: #4B3D34;
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
	background: #F9F5EC;
	width: 90%;
	max-width: 320px;
	padding: 27px 24px 50px;
	border-radius: 0;
	position: relative;
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
	background: #4B3D34;
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
	background: #4B3D34;
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
.status.invalid {
	color: #e91e63;
}
.status.error {
	color: #ff9800;
}
.status.checking {
	color: #4B3D34;
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

/* Chevron icon (for actionable rows) */
.user-info__item--action { cursor: pointer; }
.chevron {
  flex: 0 0 24px;
  width: 24px;
  height: 24px;
  color: #8a837a;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.chevron svg { width: 20px; height: 20px; }

/* 닉네임 모달 전용 보정 */
.modal--nickname {
  max-width: 360px;
  border-radius: 10px;
  padding: 27px 24px 32px;
}

/* Modal Close Button */
.modal-close-btn {
	position: absolute;
	top: 16px;
	right: 16px;
	width: 32px;
	height: 32px;
	background: transparent;
	border: none;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 4px;
	color: #666;
	transition: all 0.2s ease;
	z-index: 10;
}

.modal-close-btn:hover {
	background-color: rgba(0, 0, 0, 0.1);
	color: #333;
}

.modal-close-btn svg {
	width: 20px;
	height: 20px;
}

/* ── 알림 카드 ── */
.section-title + .notification-settings {
  margin-top: 16px; /* 12~20px 선호 */
}

.notification-settings {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(119, 107, 93, 0.1);
}

.notification-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid rgba(119, 107, 93, 0.1);
}
.notification-item:last-child { border-bottom: none; }
.notification-item__content { flex: 1; }
.notification-item__label {
  font-size: 16px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 4px;
}
.notification-item__desc {
  font-size: 14px;
  color: #4B3D34;
}
.notification-item__toggle { margin-left: 16px; }

.toggle-button {
  padding: 8px 16px;
  border: 2px solid #4B3D34;
  border-radius: 20px;
  background: #ffffff;
  color: #4B3D34;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 60px;
}
.toggle-button:hover { background: rgba(119, 107, 93, 0.1); }
.toggle-button--active { background: #4B3D34; color: #ffffff; }

.install-button {
  padding: 8px 16px;
  border: 2px solid #4caf50;
  border-radius: 20px;
  background: #ffffff;
  color: #4caf50;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 60px;
}
.install-button:hover:not(:disabled) { background: rgba(76, 175, 80, 0.1); }
.install-button:disabled {
  border-color: #cccccc;
  color: #cccccc;
  cursor: not-allowed;
}
</style>
