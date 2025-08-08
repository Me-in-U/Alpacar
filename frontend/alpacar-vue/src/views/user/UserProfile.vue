<template>
	<div class="user-profile">
		<!-- Header Component -->
		<Header />

		<!-- Main Content -->
		<div class="user-profile__content">
			<!-- Logout Section -->
			<div class="user-profile__header">
				<div class="user-profile__logout" @click="handleLogout">로그아웃</div>
			</div>

			<!-- User Info Display -->
			<div class="user-info">
				<div class="user-info__header">
					<div class="user-info__title">내 정보</div>
				</div>
				
				<div class="user-info__item">
					<div class="user-info__icon-wrapper">
						<div class="user-info__icon user-info__icon--email"></div>
					</div>
					<div class="user-info__content">
						<div class="user-info__label">이메일</div>
						<div class="user-info__value">{{ userInfo?.email || '-' }}</div>
					</div>
				</div>
				<div class="user-info__divider"></div>
				
				<div class="user-info__item">
					<div class="user-info__icon-wrapper">
						<div class="user-info__icon user-info__icon--name"></div>
					</div>
					<div class="user-info__content">
						<div class="user-info__label">이름</div>
						<div class="user-info__value">{{ userInfo?.name || '-' }}</div>
					</div>
				</div>
				<div class="user-info__divider"></div>
				
				<div class="user-info__item">
					<div class="user-info__icon-wrapper">
						<div class="user-info__icon user-info__icon--phone"></div>
					</div>
					<div class="user-info__content">
						<div class="user-info__label">전화번호</div>
						<div class="user-info__value">{{ formatPhoneNumber(userInfo?.phone) || '-' }}</div>
					</div>
				</div>
			</div>

      <!-- Vehicle Section -->
			<div class="section-header">
				<div class="section-title">내 차량정보</div>
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

			<!-- Nickname Section -->
			<div class="section-title">닉네임</div>
			<div class="input-field">
				<div class="input-field__value">{{ userInfo?.nickname }}</div>
				<div class="input-field__edit" @click="showNicknameModal = true">수정</div>
			</div>

			<!-- Phone Number Section -->
			<div class="section-title">전화번호 변경</div>
			<form autocomplete="off" @submit.prevent>
				<!-- Hidden inputs to trick browser autofill -->
				<input type="text" style="display:none" />
				<input type="password" style="display:none" />
				<input type="email" style="display:none" />
				
				<div class="input-field input-field--phone">
					<input 
						:id="'phone-' + uniqueId"
						v-model="phoneDisplay" 
						@input="handlePhoneInput" 
						@keypress="preventInvalidPhoneChars"
						@focus="onPhoneFocus"
						type="text" 
						:placeholder="phonePlaceholder" 
						class="input-field__input"
						maxlength="13"
						autocomplete="off"
						autocorrect="off"
						autocapitalize="off"
						spellcheck="false"
						:name="'phone-field-' + uniqueId"
						inputmode="numeric"
						data-form-type="other"
						data-lpignore="true"
						readonly
						onfocus="this.removeAttribute('readonly');"
					/>
				</div>
			</form>
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
				<input v-model="currentPassword" type="password" placeholder="현재 비밀번호를 입력하세요" class="input-field__input" maxlength="20"/>
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

			<!-- Notification Section -->
			<div class="section-title">알림 설정</div>
			<div class="notification-settings">
				<div class="notification-item">
					<div class="notification-item__content">
						<div class="notification-item__label">푸시 알림</div>
						<div class="notification-item__desc">주차 입출차 및 중요 알림 수신</div>
					</div>
					<div class="notification-item__toggle">
						<button 
							class="toggle-button" 
							:class="{ 'toggle-button--active': isNotificationEnabled }"
							@click="toggleNotifications"
						>
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
						<button 
							class="install-button"
							@click="installPWA"
							:disabled="!canInstallPWA"
						>
							{{ canInstallPWA ? '설치' : '설치됨' }}
						</button>
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
import { subscribeToPushNotifications, unsubscribeFromPushNotifications, getSubscriptionStatus, showLocalNotification } from "@/utils/pwa";
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
			
			// PWA 리스너 설정 및 알림 상태 확인
			setupPWAListeners();
			await checkNotificationStatus();
		} catch (e) {
			console.error("데이터 조회 오류", e);
		}
	} else {
		router.push("/login");
	}
	
	// 자동완성 방지를 위한 추가 설정
	// 컴포넌트 마운트 후 짧은 지연 시간 후 readonly 제거
	setTimeout(() => {
		const phoneInput = document.querySelector(`#phone-${uniqueId.value}`) as HTMLInputElement;
		if (phoneInput) {
			phoneInput.removeAttribute('readonly');
			phoneInput.setAttribute('autocomplete', 'off');
		}
	}, 100);
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

// 전화번호 입력란 포커스 시 readonly 속성 제거 및 자동완성 방지
const onPhoneFocus = (e: FocusEvent) => {
	const target = e.target as HTMLInputElement;
	// readonly 속성 제거
	if (target.hasAttribute('readonly')) {
		target.removeAttribute('readonly');
	}
	// 자동완성 재설정
	target.setAttribute('autocomplete', 'off');
	// 유니크 ID 재생성으로 브라우저 캐시 무효화
	uniqueId.value = Date.now();
};

// 닉네임 입력 조합 시작 (한글 입력 시작)
const onNicknameCompositionStart = () => {
	isNicknameComposing.value = true;
};

// 닉네임 입력 조합 중 업데이트 (한글 입력 중 실시간 제한)
const onNicknameCompositionUpdate = (e: CompositionEvent) => {
	const input = e.target as HTMLInputElement;
	const currentValue = input.value;
	
	// 조합 중에도 18자 초과 시 마지막 문자 제거
	if (currentValue.length > 18) {
		const truncated = currentValue.slice(0, 18);
		input.value = truncated;
		// Vue 모델도 동기화
		newNickname.value = truncated;
	}
};

// 닉네임 입력 조합 종료 (한글 입력 완료)
const onNicknameCompositionEnd = (e: Event) => {
	isNicknameComposing.value = false;
	
	// 조합이 완료된 후 18자 제한 및 특수문자 제거 적용
	const input = e.target as HTMLInputElement;
	const originalValue = input.value;
	
	// 특수문자 제거 (한글, 영문, 숫자만 허용)
	const cleaned = originalValue.replace(/[^a-zA-Z가-힣0-9]/g, "");
	
	// 최대 18자로 제한
	const truncated = cleaned.slice(0, 18);
	
	// 값이 변경된 경우 업데이트
	if (originalValue !== truncated) {
		newNickname.value = truncated;
		// DOM 업데이트를 다음 틱으로 지연
		setTimeout(() => {
			input.value = truncated;
		}, 0);
	}
};

// 닉네임 입력 핸들러 (특수문자 방지)
const handleNicknameInput = (e: Event) => {
	const input = e.target as HTMLInputElement;
	const originalValue = input.value;
	
	// 한글 조합 중이더라도 18자 초과시 잘라내기 (모바일 대응)
	if (originalValue.length > 18) {
		const truncated = originalValue.slice(0, 18);
		newNickname.value = truncated;
		input.value = truncated;
		return;
	}
	
	// 한글 입력 조합 중이면 길이 제한만 적용하고 다른 검증은 skip
	if (isNicknameComposing.value) {
		return;
	}
	
	// 특수문자 제거 (한글, 영문, 숫자만 허용)
	const cleaned = originalValue.replace(/[^a-zA-Z가-힣0-9]/g, "");
	
	// 최대 18자로 제한
	const truncated = cleaned.slice(0, 18);
	
	// 값이 변경된 경우에만 업데이트
	if (originalValue !== truncated) {
		newNickname.value = truncated;
		// 다음 틱에서 input 값 설정 (Vue의 반응성과 충돌 방지)
		setTimeout(() => {
			if (input.value !== truncated) {
				input.value = truncated;
			}
		}, 0);
	}
};

// 닉네임 길이 제한 (18자 초과 입력 방지)
const preventNicknameLengthExceed = (e: Event) => {
	const input = e.target as HTMLInputElement;
	const beforeInputEvent = e as InputEvent;
	const currentLength = input.value.length;
	
	// 입력이 문자 삽입/추가인 경우에만 길이 체크
	if (beforeInputEvent.inputType && 
		(beforeInputEvent.inputType.includes('insert') || 
		 beforeInputEvent.inputType.includes('replace') ||
		 beforeInputEvent.inputType === 'insertText' ||
		 beforeInputEvent.inputType === 'insertCompositionText')) {
		
		// 현재 18자이고 추가 입력이려는 경우 방지
		if (currentLength >= 18) {
			e.preventDefault();
			return;
		}
		
		// 입력 예정 텍스트를 고려한 길이 체크
		const inputData = beforeInputEvent.data || '';
		if (currentLength + inputData.length > 18) {
			e.preventDefault();
			return;
		}
	}
};

// 닉네임 입력 시 특수문자 방지
const preventInvalidNicknameChars = (e: KeyboardEvent) => {
	// 한글 입력 조합 중에는 키 입력을 제한하지 않음
	if (isNicknameComposing.value) {
		return;
	}
	
	const char = e.key;
	const input = e.target as HTMLInputElement;
	
	// 제어 키들은 항상 허용
	if (['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Tab', 'Enter', 'Escape'].includes(char)) {
		return;
	}
	
	// 한글 입력 시작하는 키들은 허용
	if (e.isComposing || char === 'Process') {
		return;
	}
	
	// 18자 초과 입력 방지 (한글 조합 중이 아닐 때)
	if (input.value.length >= 18) {
		e.preventDefault();
		return;
	}
	
	// 한글, 영문, 숫자만 허용
	if (!/[a-zA-Z가-힣0-9]/.test(char)) {
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

// 자동완성 방지를 위한 유니크 ID와 placeholder
const uniqueId = ref(Date.now());
const phonePlaceholder = ref("ex) 010-1234-5678");

// 한글 입력 조합 상태 관리
const isNicknameComposing = ref(false);

// PWA 및 알림 관련 상태
const isNotificationEnabled = ref(false);
const canInstallPWA = ref(false);
let deferredPrompt: any = null;

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

// 전화번호 포맷팅 함수 (01012341234 → 010-1234-1234)
const formatPhoneNumber = (phone: string | undefined | null) => {
	if (!phone) return null;
	
	// 숫자만 추출
	const digits = phone.replace(/\D/g, '');
	
	// 11자리 숫자가 아니면 원본 반환
	if (digits.length !== 11) return phone;
	
	// 010-1234-1234 형태로 포맷팅
	return digits.replace(/(\d{3})(\d{4})(\d{4})/, '$1-$2-$3');
};

// PWA 관련 함수들
// 알림 토글 - 모바일 최적화
const toggleNotifications = async () => {
	try {
		if (isNotificationEnabled.value) {
			// 알림 해제
			await unsubscribeFromPushNotifications();
			isNotificationEnabled.value = false;
			alert('푸시 알림이 해제되었습니다.');
		} else {
			// 모바일 환경 체크
			if (!('Notification' in window)) {
				alert('이 브라우저는 알림을 지원하지 않습니다.');
				return;
			}

			if (!('serviceWorker' in navigator)) {
				alert('이 브라우저는 푸시 알림을 지원하지 않습니다.');
				return;
			}

			// 권한 요청
			let permission = Notification.permission;
			if (permission === 'default') {
				permission = await Notification.requestPermission();
			}

			if (permission !== 'granted') {
				alert('알림 권한이 필요합니다. 브라우저 설정에서 알림을 허용해주세요.');
				return;
			}

			// 알림 구독
			try {
				const subscription = await subscribeToPushNotifications();
				if (subscription) {
					isNotificationEnabled.value = true;
					alert('푸시 알림이 활성화되었습니다. 주차 입출차 알림을 받을 수 있습니다.');
					
					// 테스트 알림 발송 (모바일 확인용)
					setTimeout(() => {
						showLocalNotification({
							type: 'general',
							title: '🎉 알림 설정 완료',
							body: '이제 주차 알림을 받을 수 있습니다!'
						});
					}, 1000);
				}
			} catch (error: any) {
				console.error('푸시 알림 구독 오류:', error);
				
				// 상세한 에러 메시지 제공
				let errorMessage = '푸시 알림 활성화에 실패했습니다.';
				if (error.message.includes('VAPID')) {
					errorMessage = '서버 설정 오류입니다. 관리자에게 문의하세요.';
				} else if (error.message.includes('Service Worker')) {
					errorMessage = 'HTTPS 환경에서 사용해주세요.';
				} else if (error.message.includes('권한')) {
					errorMessage = '알림 권한을 허용해주세요.';
				}
				
				alert(errorMessage);
			}
		}
	} catch (error) {
		console.error('알림 설정 변경 오류:', error);
		alert('알림 설정 변경 중 오류가 발생했습니다.');
	}
};

// PWA 설치
const installPWA = async () => {
	if (deferredPrompt) {
		try {
			deferredPrompt.prompt();
			const choiceResult = await deferredPrompt.userChoice;
			if (choiceResult.outcome === 'accepted') {
				console.log('PWA 설치 승인');
				canInstallPWA.value = false;
			} else {
				console.log('PWA 설치 거부');
			}
			deferredPrompt = null;
		} catch (error) {
			console.error('PWA 설치 오류:', error);
			alert('PWA 설치 중 오류가 발생했습니다.');
		}
	} else if (window.matchMedia('(display-mode: standalone)').matches) {
		alert('이미 PWA로 설치되어 실행 중입니다.');
	} else {
		// 모바일 브라우저에서 수동 설치 안내
		const userAgent = navigator.userAgent.toLowerCase();
		if (userAgent.includes('android')) {
			alert('Chrome 메뉴 → "홈 화면에 추가"를 선택하세요.');
		} else if (userAgent.includes('iphone') || userAgent.includes('ipad')) {
			alert('Safari 공유 버튼 → "홈 화면에 추가"를 선택하세요.');
		} else {
			alert('브라우저 메뉴에서 "앱 설치" 또는 "홈 화면에 추가"를 선택하세요.');
		}
	}
};

// 알림 상태 확인
const checkNotificationStatus = async () => {
	try {
		// 알림 권한 확인
		const hasPermission = Notification.permission === 'granted';
		
		// 구독 상태 확인
		const subscription = await getSubscriptionStatus();
		
		isNotificationEnabled.value = hasPermission && !!subscription;
		
		// PWA 설치 가능 여부 확인 - 더 정확한 감지
		const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
		const isInWebAppiOS = (window.navigator as any).standalone === true;
		const isInstalled = isStandalone || isInWebAppiOS;
		
		canInstallPWA.value = !isInstalled && (!!deferredPrompt || 'serviceWorker' in navigator);
	} catch (error) {
		console.error('알림 상태 확인 오류:', error);
	}
};

// PWA 설치 프롬프트 이벤트 리스너
const setupPWAListeners = () => {
	// PWA 설치 프롬프트 감지
	window.addEventListener('beforeinstallprompt', (e) => {
		e.preventDefault();
		deferredPrompt = e;
		canInstallPWA.value = true;
		console.log('PWA 설치 프롬프트 준비됨');
	});

	// PWA 설치 완료 감지
	window.addEventListener('appinstalled', () => {
		console.log('PWA 설치 완료');
		canInstallPWA.value = false;
		deferredPrompt = null;
	});
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
	justify-content: flex-end;
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
	background: #ffffff;
	border-radius: 16px;
	overflow: hidden;
	margin-bottom: 30px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
	border: 1px solid rgba(119, 107, 93, 0.1);
	position: relative;
}

.user-info::before {
	content: '';
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 3px;
	background: linear-gradient(90deg, #776B5D, #8B7D6B, #776B5D);
	border-radius: 16px 16px 0 0;
}

.user-info__header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20px 20px 16px 20px;
	background: linear-gradient(135deg, #f8f7f5 0%, #f5f4f2 100%);
	border-bottom: 1px solid rgba(119, 107, 93, 0.08);
}

.user-info__title {
	font-size: 18px;
	font-weight: 600;
	color: #333333;
	letter-spacing: -0.5px;
}

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
	content: '';
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

.user-info__icon--email {
	background: linear-gradient(135deg, #4285F4, #34A853);
}

.user-info__icon--email::before {
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 24 24'%3E%3Cpath d='M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.89 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z'/%3E%3C/svg%3E");
}

.user-info__icon--name {
	background: linear-gradient(135deg, #FF6B6B, #FF8E53);
}

.user-info__icon--name::before {
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 24 24'%3E%3Cpath d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E");
}

.user-info__icon--phone {
	background: linear-gradient(135deg, #00BCD4, #2196F3);
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
	color: #776B5D;
	margin-bottom: 2px;
	text-transform: capitalize;
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

/* Section Titles */
.section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 10px;
}

.section-header .button {
	margin-bottom: 0;
}

.section-title {
	font-size: 20px;
	font-weight: 600;
	margin-bottom: 0;
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

/* Notification Settings */
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

.notification-item:last-child {
	border-bottom: none;
}

.notification-item__content {
	flex: 1;
}

.notification-item__label {
	font-size: 16px;
	font-weight: 600;
	color: #333333;
	margin-bottom: 4px;
}

.notification-item__desc {
	font-size: 14px;
	color: #776B5D;
}

.notification-item__toggle {
	margin-left: 16px;
}

.toggle-button {
	padding: 8px 16px;
	border: 2px solid #776B5D;
	border-radius: 20px;
	background: #ffffff;
	color: #776B5D;
	font-size: 14px;
	font-weight: 600;
	cursor: pointer;
	transition: all 0.3s ease;
	min-width: 60px;
}

.toggle-button:hover {
	background: rgba(119, 107, 93, 0.1);
}

.toggle-button--active {
	background: #776B5D;
	color: #ffffff;
}

.install-button {
	padding: 8px 16px;
	border: 2px solid #4CAF50;
	border-radius: 20px;
	background: #ffffff;
	color: #4CAF50;
	font-size: 14px;
	font-weight: 600;
	cursor: pointer;
	transition: all 0.3s ease;
	min-width: 60px;
}

.install-button:hover:not(:disabled) {
	background: rgba(76, 175, 80, 0.1);
}

.install-button:disabled {
	border-color: #cccccc;
	color: #cccccc;
	cursor: not-allowed;
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
	
	.user-info__header {
		padding: 16px 16px 12px 16px;
	}
	
	.user-info__title {
		font-size: 16px;
	}
	
	.user-info__item {
		padding: 14px 16px;
		min-height: 56px;
	}
	
	.user-info__icon-wrapper {
		margin-right: 12px;
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
