<template>
	<div class="social-login-info-container">
		<!-- Main Content -->
		<div class="main-content">
			<!-- Page Title -->
			<div class="title-section">
				<h1 class="page-title">차량 등록을 해주세요</h1>
			</div>

			<!-- Vehicle Info Section -->
			<div class="vehicle-info-section">
				<div class="vehicle-info-card">
					<div class="vehicle-info-content">
						<div class="vehicle-info-text">
							<h2 class="vehicle-title">내 차를<br />추가해주세요</h2>
							<p class="vehicle-description">내 차종에 맞는 주차 위치를 추천해드립니다.</p>
						</div>
						<div class="vehicle-image" @click="showModal = true">
							<img src="@/assets/addcar.png" alt="차량 이미지" class="car-image" />
							<button class="add-vehicle-button" @click.stop="showModal = true" />
						</div>
					</div>
				</div>
			</div>

			<!-- Parking Skill Section -->
			<div class="parking-skill-section">
				<h2 class="skill-title">주차실력을 알려주세요</h2>
				<div class="skill-selection">
					<button class="skill-button" :class="{ selected: selectedSkill === 'advanced' }" @click="selectedSkill = 'advanced'">상급자 (좁은 공간도 가능)</button>
					<button class="skill-button" :class="{ selected: selectedSkill === 'intermediate' }" @click="selectedSkill = 'intermediate'">중급자 (보통 크기 공간)</button>
					<button class="skill-button" :class="{ selected: selectedSkill === 'beginner' }" @click="selectedSkill = 'beginner'">초급자 (넓은 공간 필요)</button>
				</div>
			</div>

			<!-- Complete Button -->
			<div class="complete-button-container">
				<button class="complete-button" @click="completeSetup">
					<span class="button-text">설정 완료</span>
				</button>
			</div>
		</div>

		<!-- Vehicle Registration Modal -->
		<div v-if="showModal" class="modal-overlay" @click="showModal = false">
			<div class="modal-content" @click.stop>
				<div class="modal-header">
					<h3 class="modal-title">차량 번호를 입력해주세요</h3>
				</div>

				<div class="modal-body">
					<input v-model="vehicleNumber" type="text" class="modal-input" placeholder="예: 12가3456" @input="handleVehicleNumberInput" maxlength="8" />
				</div>

				<!-- 실시간 중복/형식 상태 표시 -->
				<div class="license-status" v-if="vehicleNumber">
					<span v-if="plateStatus === 'checking'" class="status checking">확인 중...</span>
					<span v-else-if="plateStatus === 'ok'" class="status ok">✔ 사용 가능</span>
					<span v-else-if="plateStatus === 'duplicate'" class="status duplicate">✗ 이미 등록된 차량</span>
					<span v-else-if="plateStatus === 'error'" class="status error">검증 실패, 다시 시도</span>
					<span v-else-if="!isVehicleNumberValid" class="status error">올바른 차량번호 형식으로 입력해주세요</span>
				</div>

				<div class="modal-footer">
					<button class="modal-complete-button" @click="addVehicle" :disabled="!canAddVehicle">
						<span class="button-text">설정 완료</span>
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { BACKEND_BASE_URL } from "@/utils/api";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const userStore = useUserStore();

const showModal = ref(false);
const selectedSkill = ref("advanced");

// ── 차량번호 상태/검증 ──
const vehicleNumber = ref("");
const plateRegex = /^(?:0[1-9]|[1-9]\d|[1-9]\d{2})[가-힣][1-9]\d{3}$/;
const isVehicleNumberValid = computed(() => plateRegex.test(vehicleNumber.value));

type PlateStatus = "idle" | "checking" | "ok" | "duplicate" | "error";
const plateStatus = ref<PlateStatus>("idle");
let plateTimer: ReturnType<typeof setTimeout> | null = null;

const canAddVehicle = computed(() => isVehicleNumberValid.value && plateStatus.value === "ok");

const formData = reactive({
	vehicleNumber: "",
	parkingSkill: "advanced",
});

// 관리자 접근 차단
onMounted(() => {
	const isAdmin = userStore.me?.is_staff ?? false;
	if (isAdmin) {
		console.log("[SOCIAL-LOGIN-INFO] 관리자 접근 차단 → /admin-main");
		router.replace("/admin-main");
		return;
	}
});

// 로그인 확인
onMounted(() => {
	const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
	if (!token) {
		alert("로그인이 필요합니다.");
		router.push("/login");
	}
});

// 차량번호 입력 시 숫자/한글만 허용 + 상태 초기화
const handleVehicleNumberInput = (event: Event) => {
	const target = event.target as HTMLInputElement;
	const value = target.value;
	const cleanValue = value.replace(/[^0-9ㄱ-ㅎㅏ-ㅣ가-힣]/g, "").slice(0, 8);
	vehicleNumber.value = cleanValue;
	plateStatus.value = "idle";
};

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
			// check_license가 AllowAny라면 헤더 없이도 OK.
			// 인증이 필요한 경우, 아래 headers에 토큰을 넣어주세요.
			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/check-license/?license=${encodeURIComponent(vehicleNumber.value)}`);
			if (!res.ok) throw new Error();
			const data = await res.json();
			plateStatus.value = data.exists ? "duplicate" : "ok";
		} catch {
			plateStatus.value = "error";
		}
	}, 400);
});

// 차량 등록
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
			formData.vehicleNumber = vehicleNumber.value.trim();
			// 등록 직후 내 차량 목록 갱신이 필요하면 아래 주석 해제
			// await userStore.fetchMyVehicles();

			alert("차량 번호가 성공적으로 등록되었습니다!");
			showModal.value = false;
			vehicleNumber.value = "";
			plateStatus.value = "idle";
		} else {
			const contentType = response.headers.get("content-type");
			if (contentType && contentType.includes("application/json")) {
				const errorData = await response.json();
				alert("차량 번호 저장 실패: " + (errorData.detail || errorData.message || "서버 오류"));
				if ((errorData.detail || "").includes("이미") || response.status === 400) {
					plateStatus.value = "duplicate";
				}
			} else {
				if (response.status === 404) {
					alert("API 엔드포인트를 찾을 수 없습니다. 서버 설정을 확인해주세요.");
				} else if (response.status === 401) {
					alert("인증이 만료되었습니다. 다시 로그인해주세요.");
					router.push("/login");
				} else {
					alert("차량 번호 저장에 실패했습니다. (오류 코드: " + response.status + ")");
				}
			}
		}
	} catch (error) {
		console.error("차량 번호 저장 중 오류:", error);
		alert("차량 번호 저장 중 오류가 발생했습니다.");
		plateStatus.value = "error";
	}
};

// 설정 완료
const completeSetup = async () => {
	formData.parkingSkill = selectedSkill.value;

	if (!formData.vehicleNumber) {
		alert("차량 번호를 먼저 등록해주세요.");
		return;
	}

	try {
		const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
		if (!token) {
			alert("로그인이 필요합니다.");
			router.push("/login");
			return;
		}

		const scoreMap: Record<string, number> = { beginner: 30, intermediate: 65, advanced: 86 };
		const userScore = scoreMap[selectedSkill.value] || 30;

		const response = await fetch(`${BACKEND_BASE_URL}/user/parking-skill/`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${token}`,
			},
			body: JSON.stringify({
				parking_skill: selectedSkill.value,
				score: userScore,
			}),
		});

		if (response.ok) {
			alert(`차량 정보 설정이 완료되었습니다! (주차 점수: ${userScore}점)`);
			router.push("/main");
		} else {
			const contentType = response.headers.get("content-type");
			if (contentType && contentType.includes("application/json")) {
				const errorData = await response.json();
				alert("주차실력 저장 실패: " + (errorData.detail || errorData.message || "서버 오류"));
			} else {
				if (response.status === 404) {
					alert("API 엔드포인트를 찾을 수 없습니다. 서버 설정을 확인해주세요.");
				} else if (response.status === 401) {
					alert("인증이 만료되었습니다. 다시 로그인해주세요.");
					router.push("/login");
				} else {
					alert("주차실력 저장에 실패했습니다. (오류 코드: " + response.status + ")");
				}
			}
		}
	} catch (error) {
		console.error("주차실력 저장 중 오류:", error);
		alert("주차실력 저장 중 오류가 발생했습니다.");
	}
};
</script>

<style scoped>
.social-login-info-container {
	width: 440px;
	height: 956px;
	position: relative;
	background: #f3eeea;
	overflow: hidden;
	margin: 0 auto;
}

/* Main Content */
.main-content {
	position: relative;
	height: 100%;
	padding-top: 60px;
}

/* Title Section */
.title-section {
	position: absolute;
	left: 26px;
	top: 32px;
	margin-top: 60px;
}

.page-title {
	color: black;
	font-size: 24px;
	font-family: "Inter", sans-serif;
	font-weight: 700;
	line-height: 22px;
	margin: 0;
}

/* Vehicle Info Section */
.vehicle-info-section {
	position: absolute;
	width: 440px;
	height: 171px;
	left: 1px;
	top: 136px;
	background: white;
	overflow: hidden;
}

.vehicle-info-card {
	width: 100%;
	height: 100%;
	position: relative;
}
.vehicle-info-content {
	position: relative;
	width: 100%;
	height: 100%;
}
.vehicle-info-text {
	position: absolute;
	left: 42px;
	top: 43px;
	width: 157px;
	height: 71px;
}

.vehicle-title {
	color: #464038;
	font-size: 24px;
	font-family: "Inter", sans-serif;
	font-weight: 600;
	line-height: 32px;
	margin: 0;
}

.vehicle-description {
	width: 100%;
	color: #a0907f;
	font-size: 14px;
	font-family: "Inter", sans-serif;
	font-weight: 100;
	line-height: 18px;
	margin: 8px 0 0 0;
	white-space: nowrap;
}

.vehicle-image {
	position: absolute;
	width: 184px;
	height: 68px;
	left: 232px;
	top: 37px;
	cursor: pointer;
}

.car-image {
	width: 100%;
	height: 100%;
	object-fit: contain;
}
.add-vehicle-button {
	position: absolute;
	width: 38px;
	height: 38px;
	left: 305px;
	top: 56px;
	background: rgba(255, 255, 255, 0);
	border: none;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
}

/* Parking Skill Section */
.parking-skill-section {
	position: absolute;
	left: 26px;
	right: 26px;
	top: 349px;
	width: calc(100% - 52px);
}
.skill-title {
	color: #333333;
	font-size: 24px;
	font-family: "Inter", sans-serif;
	font-weight: 600;
	line-height: 29px;
	margin-bottom: 20px;
}

.skill-selection {
	width: 100%;
	height: 150px;
	display: flex;
	flex-direction: column;
	gap: 0;
	border: 1px solid #f3eeea;
	border-radius: 8px;
	overflow: hidden;
}
.skill-button {
	width: 100%;
	height: 50px;
	border: none;
	background-color: #ebe3d5;
	color: #4d4d4d;
	font-size: 16px;
	font-family: "Inter", sans-serif;
	font-weight: 700;
	cursor: pointer;
	transition: all 0.3s ease;
	text-align: left;
	padding: 0 15px;
}
.skill-button.selected {
	background-color: #776b5d;
	color: #f5f5f5;
}
.skill-button:hover {
	background-color: #d4c8b8;
}
.skill-button.selected:hover {
	background-color: #665a4d;
}

/* Complete Button */
.complete-button-container {
	position: absolute;
	width: 344px;
	height: 50px;
	left: 48px;
	top: 625px;
}
.complete-button {
	width: 100%;
	height: 100%;
	background: #776b5d;
	border: none;
	cursor: pointer;
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.3s ease;
}
.complete-button:hover {
	background: #665a4d;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
}
.button-text {
	color: white;
	font-size: 16px;
	font-family: "Inter", sans-serif;
	font-weight: 600;
	line-height: 19px;
}

/* Modal Styles */
.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background-color: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
}
.modal-content {
	width: 375px;
	background-color: #f3eeea;
	border-radius: 12px;
	padding: 20px;
	display: flex;
	flex-direction: column;
	gap: 16px;
}
.modal-header {
	text-align: center;
}
.modal-title {
	font-size: 18px;
	font-weight: 600;
	color: #4d4d4d;
	margin: 0;
	line-height: 22px;
}
.modal-body {
	display: flex;
	align-items: center;
}
.modal-input {
	width: 100%;
	height: 50px;
	background-color: #ffffff;
	border: 1px solid #cccccc;
	border-radius: 8px;
	padding: 0 15px;
	font-size: 16px;
	font-weight: 400;
	color: #333333;
	outline: none;
	transition: border-color 0.3s ease;
	box-sizing: border-box;
}
.modal-input::placeholder {
	color: #999999;
}
.modal-input:focus {
	border-color: #776b5d;
}
.modal-footer {
	display: flex;
	justify-content: center;
}
.modal-complete-button {
	width: 280px;
	height: 50px;
	background-color: #776b5d;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.3s ease;
	display: flex;
	align-items: center;
	justify-content: center;
}
.modal-complete-button:hover {
	background-color: #665a4d;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
}

/* ── 추가: 상태 표시 스타일 ── */
.license-status {
	margin: -6px 0 6px 0;
	min-height: 20px;
	display: flex;
	align-items: center;
	font-size: 14px;
	font-weight: 600;
	gap: 6px;
	justify-content: center;
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

.error-message {
	color: #f44336;
	font-size: 14px;
	text-align: center;
}

/* Responsive Design */
@media (max-width: 440px) {
	.social-login-info-container {
		width: 100vw;
		height: 100vh;
	}
	.vehicle-info-section {
		width: 100%;
	}
	.parking-skill-section {
		left: 26px;
		right: 26px;
		width: calc(100% - 52px);
	}
	.skill-selection {
		width: 100%;
	}
	.complete-button-container {
		width: calc(100% - 96px);
		left: 48px;
	}
}

@media (min-width: 441px) {
	.social-login-info-container {
		width: 440px;
		margin: 0 auto;
	}
}
</style>
