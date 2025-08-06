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

			<!-- Phone Number Section -->
			<div class="section-title">전화번호 변경</div>
			<div class="section-subtitle">새 전화번호 입력</div>
			<div class="input-field input-field--phone">
				<input 
					v-model="phoneDisplay" 
					@input="handlePhoneInput" 
					@keypress="preventInvalidPhoneChars"
					type="tel" 
					placeholder="ex) 010-1234-5678" 
					class="input-field__input"
					maxlength="13"
					autocomplete="nope"
					autocorrect="off"
					autocapitalize="off"
					spellcheck="false"
					name="new-phone-number"
					inputmode="numeric"
				/>
			</div>
			<div v-if="newPhoneNumber && !isPhoneValid" class="error-message">
				올바른 전화번호 형식으로 입력해주세요 (숫자 11자리)
			</div>

			<!-- Change Phone Button -->
			<div class="button-container">
				<div class="button button--primary" @click="requestPhoneChange">
					<div class="button__text">변경하기</div>
				</div>
			</div>

			<!-- Password Section -->
			<div class="section-title">비밀번호 변경</div>
			<div class="section-subtitle">현재 비밀번호 입력</div>
			<div class="input-field input-field--password">
				<input v-model="currentPassword" type="password" placeholder="현재 비밀번호를 입력하세요" class="input-field__input" />
			</div>

			<div class="section-subtitle">새 비밀번호 입력</div>
			<div class="input-field input-field--password">
				<input v-model="newPassword" type="password" placeholder="새 비밀번호를 입력하세요" class="input-field__input" maxlength="20" />
			</div>
			<ul v-if="newPassword && !isPasswordValid" class="password-rules">
				<li :class="passwordLengthValid ? 'valid' : 'invalid'">8~20자</li>
				<li :class="passwordLetterValid ? 'valid' : 'invalid'">문자 포함</li>
				<li :class="passwordNumberValid ? 'valid' : 'invalid'">숫자 포함</li>
				<li :class="passwordSpecialValid ? 'valid' : 'invalid'">특수문자 포함</li>
				<li :class="passwordNoTripleValid ? 'valid' : 'invalid'">동일문자 3연속 불가</li>
				<li :class="passwordNoSeqValid ? 'valid' : 'invalid'">연속문자 3연속 불가</li>
			</ul>

			<div class="section-subtitle">새 비밀번호 확인</div>
			<div class="input-field input-field--password">
				<input v-model="confirmPassword" type="password" placeholder="새 비밀번호를 다시 입력하세요" class="input-field__input" maxlength="20" />
			</div>
			<div v-if="confirmPassword && !isPasswordConfirmValid" class="error-message">
				비밀번호가 일치하지 않습니다
			</div>

			<!-- Change Password Button -->
			<div class="button-container">
				<div class="button button--primary" @click="requestPasswordChange">
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
					<img 
						:src="getVehicleImageUrl(vehicle.model?.image_url)" 
						alt="차량 이미지" 
						class="vehicle-card__image" 
						@error="(e) => (e.target as HTMLImageElement).src = defaultCarImage"
					/>
					<div class="vehicle-card__info">
						<div><strong>번호판:</strong> {{ vehicle.license_plate }}</div>
						<div><strong>모델:</strong> {{ vehicle.model?.brand || '알파카' }} {{ vehicle.model?.model_name || '차량' }}</div>
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
					<input 
						v-model="newNickname" 
						@input="handleNicknameInput"
						@keypress="preventInvalidNicknameChars"
						type="text" 
						placeholder="예: 주차하는 알파카" 
						class="modal__input"
						maxlength="18" 
					/>
				</div>
				<div v-if="newNickname && !isNicknameValid" class="error-message">
					닉네임은 한글, 영문, 숫자만 사용 가능 (2-18자)
				</div>
				<button class="modal__button" @click="updateNickname" :disabled="!isNicknameValid">설정 완료</button>
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

		<!-- Vehicle Add Modal (Simplified) -->
		<div v-if="showVehicleModal" class="modal-overlay" @click="showVehicleModal = false">
			<div class="modal modal--vehicle" @click.stop>
				<h3 class="modal__title">차량 번호를 입력하세요</h3>
				
				<div class="modal__input-field">
					<input 
						v-model="vehicleNumber" 
						type="text" 
						placeholder="예: 12가3456" 
						class="modal__input"
						@input="handleVehicleNumberInput"
						maxlength="8"
					/>
				</div>
				
				<div class="license-check-section">
					<button 
						class="license-check-button" 
						@click="checkVehicleDuplicate" 
						:disabled="!vehicleNumber || !isVehicleNumberValid"
					>
						중복체크
					</button>
					<span v-if="vehicleChecked && !isDuplicate" class="check-success">✔ 사용가능</span>
					<span v-if="vehicleChecked && isDuplicate" class="check-error">✗ 이미 등록된 차량</span>
				</div>
				
				<div v-if="vehicleNumber && !isVehicleNumberValid" class="error-message">
					올바른 차량번호 형식으로 입력해주세요
				</div>

				<button 
					class="modal__button" 
					@click="addSimpleVehicle" 
					:disabled="!canAddVehicle"
				>
					등록완료
				</button>
			</div>
		</div>

		<!-- Email Verification Modal -->
		<div v-if="showEmailVerificationModal" class="modal-overlay" @click="showEmailVerificationModal = false">
			<div class="modal modal--email-verify" @click.stop>
				<h3 class="modal__title">
					{{ verificationTarget === 'phone' ? '전화번호 변경' : '비밀번호 변경' }} 인증
				</h3>
				
				<div class="email-info">
					<span>{{ userInfo?.email }}로 인증번호를 발송합니다.</span>
				</div>
				
				<div class="verification-step">
					<button 
						class="modal__button" 
						@click="sendEmailVerification"
						:disabled="emailSent"
					>
						{{ emailSent ? '인증번호 발송됨' : '인증번호 발송' }}
					</button>
				</div>
				
				<div v-if="emailSent" class="verification-input">
					<div class="modal__input-field">
						<input 
							v-model="verificationCode" 
							type="text" 
							placeholder="인증번호를 입력하세요" 
							class="modal__input"
							maxlength="6"
						/>
					</div>
					
					<button 
						class="modal__button" 
						@click="verifyEmailCode"
						:disabled="!verificationCode || emailVerified"
					>
						{{ emailVerified ? '인증완료' : '인증확인' }}
					</button>
				</div>
				
				<div v-if="emailVerified" class="verification-complete">
					<button 
						class="modal__button modal__button--success" 
						@click="verificationTarget === 'phone' ? executePhoneChange() : confirmPasswordChange()"
					>
						{{ verificationTarget === 'phone' ? '전화번호 변경' : '비밀번호 변경' }} 완료
					</button>
				</div>
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
import { BACKEND_BASE_URL } from "@/utils/api";
import defaultCarImage from "@/assets/alpaka_in_car.png";

const router = useRouter();
const userStore = useUserStore();

// ---- 간소화된 차량 추가 폼 상태 ----
const vehicleNumber = ref("");
const vehicleChecked = ref(false);
const isDuplicate = ref(false);

// 번호판 정규식
const plateRegex = /^(?:0[1-9]|[1-9]\d|[1-9]\d{2})[가-힣][1-9]\d{3}$/;

// 차량번호 유효성 검사
const isVehicleNumberValid = computed(() => plateRegex.test(vehicleNumber.value));
const canAddVehicle = computed(() => isVehicleNumberValid.value && vehicleChecked.value && !isDuplicate.value);

// 전화번호 유효성 검사 (11자리 숫자만)
const isPhoneValid = computed(() => /^[0-9]{11}$/.test(newPhoneNumber.value));

// 닉네임 유효성 검사 (한글, 영문, 숫자만 허용, 2-18자)
const isNicknameValid = computed(() => {
	const noSpecialChars = /^[a-zA-Z가-힣0-9]+$/.test(newNickname.value);
	const lengthValid = newNickname.value.length >= 2 && newNickname.value.length <= 18;
	return noSpecialChars && lengthValid;
});

// 비밀번호 유효성 검사 (8-20자, 문자/숫자/특수문자 포함, 동일문자 3연속 불가, 연속문자 3연속 불가)
const passwordLengthValid = computed(() => newPassword.value.length >= 8 && newPassword.value.length <= 20);
const passwordLetterValid = computed(() => /[a-zA-Z]/.test(newPassword.value));
const passwordNumberValid = computed(() => /\d/.test(newPassword.value));
const passwordSpecialValid = computed(() => /[$@!%*#?&/]/.test(newPassword.value));
const passwordNoTripleValid = computed(() => !/(\w)\1\1/.test(newPassword.value));
const passwordNoSeqValid = computed(() => {
	for (let i = 0; i < newPassword.value.length - 2; i++) {
		const a = newPassword.value.charCodeAt(i),
			b = newPassword.value.charCodeAt(i + 1),
			c = newPassword.value.charCodeAt(i + 2);
		if ((b === a + 1 && c === b + 1) || (b === a - 1 && c === b - 1)) {
			return false;
		}
	}
	return true;
});
const isPasswordValid = computed(() => 
	[passwordLengthValid, passwordLetterValid, passwordNumberValid, passwordSpecialValid, passwordNoTripleValid, passwordNoSeqValid].every((v) => v.value)
);
const isPasswordConfirmValid = computed(() => confirmPassword.value === newPassword.value && confirmPassword.value.length > 0);

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
// 전화번호 입력 핸들러 (숫자만 허용, 3-4-4 포맷)
const handlePhoneInput = (e: Event) => {
	// 입력값에서 숫자만 추출
	let digits = (e.target as HTMLInputElement).value.replace(/[^0-9]/g, "");
	if (digits.length > 11) digits = digits.slice(0, 11);
	// 화면용: 3-4-4 포맷
	const part1 = digits.slice(0, 3);
	const part2 = digits.length >= 4 ? digits.slice(3, 7) : "";
	const part3 = digits.length >= 8 ? digits.slice(7) : "";
	phoneDisplay.value = [part1, part2, part3].filter(Boolean).join("-");
	// 실제 전송용: 숫자만
	newPhoneNumber.value = digits;
};

// 전화번호 입력 시 숫자 이외 문자 방지
const preventInvalidPhoneChars = (e: KeyboardEvent) => {
	const char = e.key;
	// 숫자, 백스페이스, 방향키 등만 허용
	if (!/[0-9]/.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(char)) {
		e.preventDefault();
	}
};

// 닉네임 입력 핸들러 (특수문자 방지)
const handleNicknameInput = (e: Event) => {
	const input = e.target as HTMLInputElement;
	// 특수문자 제거 (한글, 영문, 숫자만 허용)
	const cleaned = input.value.replace(/[^a-zA-Z가-힣0-9]/g, "");
	// 최대 18자로 제한
	newNickname.value = cleaned.slice(0, 18);
	input.value = newNickname.value;
};

// 닉네임 입력 시 특수문자 방지
const preventInvalidNicknameChars = (e: KeyboardEvent) => {
	const char = e.key;
	// 한글, 영문, 숫자, 백스페이스 등만 허용
	if (!/[a-zA-Z가-힣0-9]/.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(char)) {
		e.preventDefault();
	}
};

// 차량번호 입력 핸들러 (숫자와 한글만 허용)
const handleVehicleNumberInput = (event: Event) => {
	const target = event.target as HTMLInputElement;
	const value = target.value;
	const cleanValue = value.replace(/[^0-9ㄱ-ㅎㅏ-ㅣ가-힣]/g, '');
	if (cleanValue.length > 8) {
		vehicleNumber.value = cleanValue.substring(0, 8);
	} else {
		vehicleNumber.value = cleanValue;
	}
	// 입력이 변경되면 중복체크 상태 초기화
	vehicleChecked.value = false;
	isDuplicate.value = false;
};

// 차량번호 중복체크
const checkVehicleDuplicate = async () => {
	if (!isVehicleNumberValid.value) {
		alert("올바른 차량번호 형식으로 입력해주세요.");
		return;
	}
	
	try {
		const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
		const response = await fetch(`${BACKEND_BASE_URL}/vehicles/check-license/?license=${encodeURIComponent(vehicleNumber.value)}`, {
			method: 'GET',
			headers: {
				'Authorization': `Bearer ${token}`,
				'Content-Type': 'application/json'
			}
		});
		
		if (!response.ok) {
			throw new Error(`API 오류: ${response.status}`);
		}
		
		const data = await response.json();
		vehicleChecked.value = true;
		// API 응답 구조: { exists: boolean }
		// exists가 true면 이미 존재 = 중복
		isDuplicate.value = data.exists === true;
		alert(isDuplicate.value ? "이미 등록된 차량번호입니다." : "사용 가능한 차량번호입니다.");
	} catch (error) {
		console.error('중복체크 오류:', error);
		alert('차량번호 중복체크 중 오류가 발생했습니다.');
		// 에러시에는 체크 상태를 유지하지 않음
		vehicleChecked.value = false;
		isDuplicate.value = false;
	}
};

// 간소화된 차량 추가
const addSimpleVehicle = async () => {
	if (!canAddVehicle.value) {
		alert("차량번호를 입력하고 중복체크를 완료해주세요.");
		return;
	}
	
	try {
		const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
		const response = await fetch(`${BACKEND_BASE_URL}/vehicles/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${token}`
			},
			body: JSON.stringify({
				license_plate: vehicleNumber.value,
				model: 1  // Default model ID (backend will assign actual model)
			})
		});
		
		if (response.ok) {
			alert("차량이 성공적으로 등록되었습니다.");
			showVehicleModal.value = false;
			vehicleNumber.value = "";
			vehicleChecked.value = false;
			isDuplicate.value = false;
			// 차량 목록 새로고침
			await userStore.fetchMyVehicles();
		} else {
			const errorData = await response.json();
			alert("차량 등록 실패: " + (errorData.detail || errorData.message || "서버 오류"));
		}
	} catch (error) {
		console.error('차량 등록 오류:', error);
		alert('차량 등록 중 오류가 발생했습니다.');
	}
};
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
const showPhoneChangeModal = ref(false);
const showEmailVerificationModal = ref(false);

const newNickname = ref("");
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const newPhoneNumber = ref("");
const phoneDisplay = ref("");

// 이메일 인증 관련
const verificationCode = ref("");
const emailSent = ref(false);
const emailVerified = ref(false);
const verificationTarget = ref<'phone' | 'password'>('phone');

const vehicleForm = ref<{ number: string }>({ number: "" });

// 이미지 URL 처리 함수 - 로컬 개발환경에서 포트 문제 해결
const getVehicleImageUrl = (imageUrl: string | undefined) => {
	if (!imageUrl) return defaultCarImage;
	
	// 절대 URL인 경우 (http:// 또는 https://로 시작) 그대로 사용
	if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
		return imageUrl;
	}
	
	// 상대 URL인 경우 백엔드 베이스 URL과 결합
	// imageUrl이 /로 시작하지 않으면 /를 추가
	const cleanImageUrl = imageUrl.startsWith('/') ? imageUrl : `/${imageUrl}`;
	
	// BACKEND_BASE_URL이 /api로 끝나는 경우 제거하고 이미지 URL 추가
	const backendUrl = BACKEND_BASE_URL.replace(/\/api$/, '');
	return `${backendUrl}${cleanImageUrl}`;
};

// Methods
// Logout
const handleLogout = () => {
	userStore.clearUser();
	router.push("/login");
};

const updateNickname = async () => {
	const nick = newNickname.value.trim();
	if (!nick) return alert("닉네임을 입력해주세요.");

	try {
		await userStore.updateProfile({ nickname: nick });
		alert("닉네임이 변경되었습니다.");
		showNicknameModal.value = false;
		newNickname.value = "";
	} catch (err: any) {
		console.error("닉네임 변경 실패:", err);
		alert("변경 실패: " + err.message);
	}
};

// 이메일 인증번호 발송
const sendEmailVerification = async () => {
	try {
		const response = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/request/`, {
			method: "POST",
			headers: { 
				"Content-Type": "application/json",
				"Authorization": `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
			},
			body: JSON.stringify({ email: userInfo.value?.email }),
		});
		
		if (response.ok) {
			emailSent.value = true;
			alert("인증번호를 발송했습니다.");
		} else {
			alert("인증번호 발송 실패");
		}
	} catch {
		alert("인증번호 발송 실패");
	}
};

// 인증번호 확인
const verifyEmailCode = async () => {
	try {
		const response = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/verify/`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ email: userInfo.value?.email, code: verificationCode.value }),
		});
		
		if (response.ok) {
			emailVerified.value = true;
			alert("이메일 인증이 완료되었습니다.");
		} else {
			const error = await response.json();
			alert(error.detail || "인증 실패");
		}
	} catch (err: any) {
		alert("인증 실패");
	}
};

// 전화번호 변경 요청
const requestPhoneChange = () => {
	if (!newPhoneNumber.value.trim()) {
		alert("새 전화번호를 입력해주세요.");
		return;
	}
	verificationTarget.value = 'phone';
	emailSent.value = false;
	emailVerified.value = false;
	verificationCode.value = "";
	showEmailVerificationModal.value = true;
};

// 전화번호 변경 실행
const executePhoneChange = async () => {
	if (!emailVerified.value) {
		alert("이메일 인증을 먼저 완료해주세요.");
		return;
	}
	
	if (!newPhoneNumber.value || !isPhoneValid.value) {
		alert("올바른 전화번호를 입력해주세요.");
		return;
	}
	
	try {
		const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
		// Using /users/me/ endpoint with PUT method like updateProfile in store
		const response = await fetch(`${BACKEND_BASE_URL}/users/me/`, {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${token}`
			},
			body: JSON.stringify({ 
				phone: newPhoneNumber.value,
				// Include current values to avoid overwriting
				nickname: userInfo.value?.nickname,
				name: userInfo.value?.name
			})
		});
		
		if (response.ok) {
			alert("전화번호가 성공적으로 변경되었습니다.");
			// Reset states
			showEmailVerificationModal.value = false;
			newPhoneNumber.value = "";
			phoneDisplay.value = "";
			emailSent.value = false;
			emailVerified.value = false;
			verificationCode.value = "";
			// Refresh user data
			await userStore.fetchMe(token!);
		} else {
			const errorData = await response.json();
			alert("전화번호 변경 실패: " + (errorData.detail || errorData.message || "서버 오류"));
		}
	} catch (error) {
		console.error('전화번호 변경 오류:', error);
		alert('전화번호 변경 중 오류가 발생했습니다.');
	}
};

// 비밀번호 변경 요청 (이메일 인증 필요)
const requestPasswordChange = () => {
	verificationTarget.value = 'password';
	emailSent.value = false;
	emailVerified.value = false;
	verificationCode.value = "";
	showEmailVerificationModal.value = true;
};

const confirmPasswordChange = async () => {
	if (!emailVerified.value) {
		alert("이메일 인증을 먼저 완료해주세요.");
		return;
	}

	const cur = currentPassword.value;
	const neu = newPassword.value;
	const cf = confirmPassword.value;

	if (!cur || !neu || !cf) {
		return alert("모든 비밀번호 필드를 입력해주세요.");
	}
	if (neu !== cf) {
		return alert("새 비밀번호가 일치하지 않습니다.");
	}

	try {
		await userStore.changePassword(cur, neu);
		alert("비밀번호가 성공적으로 변경되었습니다.");
		showEmailVerificationModal.value = false;
	} catch (err: any) {
		console.error("비밀번호 변경 실패:", err);
		alert("변경 실패: " + err.message);
	} finally {
		showPasswordConfirmModal.value = false;
		currentPassword.value = "";
		newPassword.value = "";
		confirmPassword.value = "";
	}
};

const removeVehicle = async (id: number) => {
	// 차량이 1대만 있는 경우 삭제 방지
	if (vehicles.value.length <= 1) {
		showSingleVehicleWarning.value = true;
		return;
	}
	
	if (!confirm("차량을 정말 삭제하시겠습니까?")) return;
	
	try {
		await userStore.removeVehicle(id);
		alert("차량이 삭제되었습니다.");
	} catch (error) {
		console.error('차량 삭제 오류:', error);
		alert('차량 삭제 중 오류가 발생했습니다.');
	}
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
	height: 150px;
	background: #fff;
	border: 1px solid #ccc;
	border-radius: 10px;
	padding: 0 14px;
	margin-bottom: 15px;
}
.vehicle-card__image {
	width: 120px;
	height: 100px;
	object-fit: contain;
	border-radius: 5px;
	margin-right: 12px;
	background-color: transparent;
	flex-shrink: 0;
	padding: 2px;
}
.vehicle-card__info {
	font-size: 18px;
	white-space: normal;
	flex: 1;
	min-width: 0;
}
.vehicle-card__actions {
	display: flex;
	gap: 12px;
}
.vehicle-card__edit,
.vehicle-card__delete {
	font-size: 16px;
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

/* Vehicle Modal Specific Styles */
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

/* Email Verification Modal Styles */
.email-info {
	text-align: center;
	margin-bottom: 20px;
	font-size: 14px;
	color: #666;
}

.verification-step {
	margin-bottom: 20px;
}

.verification-input {
	margin-bottom: 20px;
}

.verification-complete {
	margin-top: 20px;
}

.modal__button--success {
	background: #4caf50;
}

/* Password validation rules */
.password-rules {
	list-style: none;
	padding: 0;
	margin: 5px 0 15px 0;
	font-size: 12px;
}

.password-rules li {
	padding: 2px 0;
	color: #999;
}

.password-rules li.valid {
	color: #4caf50;
}

.password-rules li.valid::before {
	content: "✓ ";
}

.password-rules li.invalid {
	color: #f44336;
}

.password-rules li.invalid::before {
	content: "✗ ";
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
