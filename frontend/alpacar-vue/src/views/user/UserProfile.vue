<template>
	<div class="user-profile">
		<!-- Header Component -->
		<Header />

		<!-- Main Content -->
		<div class="user-profile__content">
			<!-- Title and Logout Section -->
			<div class="user-profile__header">
				<h1 class="user-profile__title">내 정보 확인하기</h1>
				<div class="user-profile__logout" @click="handleLogout">로그아웃</div>
			</div>

			<!-- User Info Display -->
			<div class="user-info">
				<div class="user-info__label">이메일</div>
				<div class="user-info__value">{{ userInfo?.email }}</div>
				<div class="user-info__label">이름</div>
				<div class="user-info__value">{{ userInfo?.name }}</div>
				<div class="user-info__label">전화번호</div>
				<div class="user-info__value">{{ userInfo?.phone }}</div>
			</div>

			<!-- Nickname Section -->
			<div class="section-title">닉네임</div>
			<div class="input-field">
				<div class="input-field__value">{{ userInfo?.nickname }}</div>
				<div class="input-field__edit" @click="showNicknameModal = true">수정</div>
			</div>

			<!-- Password Section -->
			<div class="section-title">비밀번호 변경</div>
			<div class="section-subtitle">현재 비밀번호 입력</div>
			<div class="input-field input-field--password">
				<input v-model="currentPassword" type="password" placeholder="현재 비밀번호를 입력하세요" class="input-field__input" />
			</div>

			<div class="section-subtitle">새 비밀번호 입력</div>
			<div class="input-field input-field--password">
				<input v-model="newPassword" type="password" placeholder="새 비밀번호를 입력하세요" class="input-field__input" />
			</div>

			<div class="section-subtitle">새 비밀번호 확인</div>
			<div class="input-field input-field--password">
				<input v-model="confirmPassword" type="password" placeholder="새 비밀번호를 다시 입력하세요" class="input-field__input" />
			</div>

			<!-- Change Password Button -->
			<div class="button-container">
				<div class="button button--primary" @click="showPasswordConfirmModal = true">
					<div class="button__text">변경하기</div>
				</div>
			</div>

			<!-- Vehicle Section -->
			<div class="section-title">내 차량정보</div>
			<div class="button-container">
				<div class="button button--secondary" @click="showVehicleModal = true">
					<div class="button__text">내 차 추가</div>
				</div>
			</div>

			<!-- Vehicle List -->
			<div class="vehicle-list">
				<div v-for="vehicle in displayedVehicles" :key="vehicle.id" class="vehicle-card">
					<img :src="vehicle.model.image_url" alt="차량 이미지" />
					<div class="vehicle-card__info">
						<div><strong>번호판:</strong> {{ vehicle.license_plate }}</div>
						<div><strong>모델:</strong> {{ vehicle.model.brand }} {{ vehicle.model.model_name }}</div>
					</div>
					<div class="vehicle-card__actions">
						<div class="vehicle-card__delete" @click="removeVehicle(vehicle.id)">삭제</div>
					</div>
				</div>
			</div>

			<!-- More/Less Button -->
			<div class="button-container" v-if="vehicles.length > 3">
				<div class="button button--more" @click="showAllVehicles = !showAllVehicles">
					<div class="button__text">
						{{ showAllVehicles ? "접기" : `더보기 (${vehicles.length - 3})` }}
					</div>
				</div>
			</div>
		</div>

		<!-- Bottom Navigation -->
		<BottomNavigation />

		<!-- Nickname Edit Modal -->
		<div v-if="showNicknameModal" class="modal-overlay" @click="showNicknameModal = false">
			<div class="modal modal--nickname" @click.stop>
				<h3 class="modal__title">수정할 닉네임을 입력하세요</h3>
				<div class="modal__input-field">
					<input v-model="newNickname" type="text" placeholder="예: 주차하는 알파카" class="modal__input" />
				</div>
				<button class="modal__button" @click="updateNickname">설정 완료</button>
			</div>
		</div>

		<!-- Password Change Confirmation Modal -->
		<div v-if="showPasswordConfirmModal" class="modal-overlay" @click="showPasswordConfirmModal = false">
			<div class="modal modal--password-confirm" @click.stop>
				<h3 class="modal__title">비밀번호를 변경하시겠습니까?</h3>
				<div class="modal__buttons">
					<button class="modal__button modal__button--left" @click="confirmPasswordChange">예</button>
					<button class="modal__button modal__button--right" @click="showPasswordConfirmModal = false">아니오</button>
				</div>
			</div>
		</div>

		<!-- Vehicle Add/Edit Modal -->
		<div v-if="showVehicleModal" class="modal-overlay" @click="showVehicleModal = false">
			<div class="modal modal--vehicle" @click.stop>
				<h3 class="modal__title">내 차 추가하기</h3>

				<!-- 제조사 / 모델 선택 -->
				<label>제조사 선택</label>
				<select v-model="selectedBrand" @change="onBrandChange">
					<option value="">-- 제조사 선택 --</option>
					<option v-for="b in brands" :key="b">{{ b }}</option>
				</select>

				<label>모델 선택</label>
				<select v-model.number="selectedModelId" :disabled="!selectedBrand">
					<option value="">-- 모델 선택 --</option>
					<option v-for="m in filteredModels" :key="m.id" :value="m.id">
						{{ m.model_name }}
					</option>
				</select>
				<img v-if="selectedModelImage" :src="selectedModelImage" class="modal__vehicle-img" />

				<!-- 번호판 입력 & 중복 체크 -->
				<label>차량 번호 입력</label>
				<div style="display: flex; align-items: center">
					<input v-model="license" placeholder="예: 12가3456" />
					<button @click="onCheckLicense" :disabled="!license">중복체크</button>
					<span v-if="licenseOk" style="color: #4caf50; margin-left: 8px">✔</span>
				</div>
				<small v-show="license && !licenseValid" style="color: red"> 번호판 형식이 올바르지 않습니다. </small>

				<button class="modal__button" @click="onAddVehicle" :disabled="!canSubmit">설정 완료</button>
			</div>
		</div>

		<!-- Single Vehicle Warning Modal -->
		<div v-if="showSingleVehicleWarning" class="modal-overlay" @click="showSingleVehicleWarning = false">
			<div class="modal modal--warning" @click.stop>
				<h3 class="modal__title">차량이 1대밖에 없어 삭제할 수 없습니다.</h3>
				<button class="modal__button" @click="showSingleVehicleWarning = false">확인</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const router = useRouter();
const userStore = useUserStore();
// ---- 내 차 추가 폼 상태 ----
const selectedBrand = ref("");
const selectedModelId = ref<number | null>(null);
const license = ref("");
const licenseOk = ref(false);

// 번호판 정규식
const plateRegex = /^(?:0[1-9]|[1-9]\d|[1-9]\d{2})[가-힣][1-9]\d{3}$/;

// 브랜드 목록
const brands = computed(() => Array.from(new Set(userStore.vehicleModels.map((m) => m.brand))));
// 모델 필터링
const filteredModels = computed(() => userStore.vehicleModels.filter((m) => m.brand === selectedBrand.value));
// 선택된 모델 이미지
const selectedModelImage = computed(() => {
	const m = userStore.vehicleModels.find((m) => m.id === selectedModelId.value);
	return m?.image_url || "";
});

// 유효성
const licenseValid = computed(() => plateRegex.test(license.value));
const canSubmit = computed(() => selectedModelId.value && licenseValid.value && licenseOk.value);

// 마운트 시 프로필·차량 목록 함께 불러오기
onMounted(async () => {
	const token = localStorage.getItem("access_token");
	if (token) {
		try {
			await userStore.fetchMe(token);
			await userStore.fetchMyVehicles();
			await userStore.fetchVehicleModels();
		} catch (e) {
			console.error("데이터 조회 오류", e);
		}
	} else {
		router.push("/login");
	}
});
// 브랜드 변경 시
function onBrandChange() {
	selectedModelId.value = null;
} // 중복 체크
async function onCheckLicense() {
	if (!licenseValid.value) {
		alert("올바른 번호판 형식으로 입력해주세요.");
		return;
	}
	licenseOk.value = await userStore.checkLicense(license.value);
	alert(licenseOk.value ? "사용 가능" : "이미 등록됨");
} // 차량 추가
async function onAddVehicle() {
	try {
		await userStore.addVehicle(selectedModelId.value!, license.value);
		alert("차량이 추가되었습니다.");
		showVehicleModal.value = false;
	} catch (err: any) {
		alert("추가 실패: " + err.message);
	}
}
// userInfo & vehicles
const userInfo = computed(() => userStore.me);
const vehicles = computed(() => userStore.vehicles);

// "더보기"/"접기" 처리
const showAllVehicles = ref(false);
const displayedVehicles = computed(() => (vehicles.value.length <= 3 ? vehicles.value : showAllVehicles.value ? vehicles.value : vehicles.value.slice(0, 3)));

// Modal States & Form Data
const showNicknameModal = ref(false);
const showPasswordConfirmModal = ref(false);
const showVehicleModal = ref(false);
const showDeleteModal = ref(false);
const showSingleVehicleWarning = ref(false);

const newNickname = ref("");
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");

const vehicleForm = ref<{ number: string }>({ number: "" });

// Methods
// Logout
const handleLogout = () => {
	userStore.clearUser();
	router.push("/login");
};

const updateNickname = async () => {
	if (!newNickname.value.trim()) return alert("닉네임을 입력해주세요.");
	userStore.me!.nickname = newNickname.value.trim();
	showNicknameModal.value = false;
	newNickname.value = "";
	alert("닉네임이 변경되었습니다.");
};

const confirmPasswordChange = () => {
	if (currentPassword.value && newPassword.value && confirmPassword.value) {
		if (newPassword.value === confirmPassword.value) {
			console.log("비밀번호 변경:", { current: currentPassword.value, new: newPassword.value });
			alert("비밀번호가 변경되었습니다.");
		} else alert("새 비밀번호가 일치하지 않습니다.");
	} else alert("모든 비밀번호 필드를 입력해주세요.");
	showPasswordConfirmModal.value = false;
	currentPassword.value = "";
	newPassword.value = "";
	confirmPassword.value = "";
};

const removeVehicle = async (id: number) => {
	if (!confirm("차량을 정말 삭제하시겠습니까?")) return;
	await userStore.removeVehicle(id);
};
</script>

<style scoped>
/* ── 전체 레이아웃 ── */
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

/* Header */
.user-profile__header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}
.user-profile__title {
	font-size: 24px;
	font-weight: 700;
}
.user-profile__logout {
	font-size: 16px;
	cursor: pointer;
}

/* User Info */
.user-info {
	background: #ebe3d5;
	border-radius: 10px;
	padding: 10px;
	margin-bottom: 20px;
}
.user-info__label {
	font-size: 16px;
	margin-bottom: 4px;
}
.user-info__value {
	font-size: 16px;
}

/* Section Titles */
.section-title {
	font-size: 20px;
	font-weight: 600;
	margin-bottom: 10px;
}
.section-subtitle {
	font-size: 16px;
	font-weight: 600;
	margin: 0 0 10px;
}

/* ── Input Field ── */
.input-field {
	display: flex;
	align-items: center;
	justify-content: space-between;
	height: 48px;
	background: #fff;
	border: 1px solid #ccc;
	border-radius: 10px;
	padding: 0 14px;
	margin-bottom: 20px;
}
.input-field__value {
	font-size: 16px;
	white-space: normal;
}
.input-field__edit {
	font-size: 12px;
	cursor: pointer;
	white-space: nowrap;
}
.input-field__input {
	width: 100%;
	border: none;
	outline: none;
	font-size: 16px;
}

/* ── Buttons ── */
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
.button--primary,
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

/* ── Vehicle Card ── */
.vehicle-list {
	margin-top: 10px;
}
.vehicle-card {
	display: flex;
	align-items: center;
	justify-content: space-between;
	height: 75px;
	background: #fff;
	border: 1px solid #ccc;
	border-radius: 10px;
	padding: 0 14px;
	margin-bottom: 15px;
}
.vehicle-card__info {
	font-size: 14px;
	white-space: normal;
}
.vehicle-card__actions {
	display: flex;
	gap: 12px;
}
.vehicle-card__edit,
.vehicle-card__delete {
	font-size: 11px;
	cursor: pointer;
}

/* ── Modal 공통 ── */
.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
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

/* ── Responsive (데스크톱 vs 모바일) ── */
@media (max-width: 440px) {
	.user-profile {
		width: 100vw;
		height: 100vh;
	}

	.user-profile__content {
		padding-left: 15px;
		padding-right: 15px;
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
