<template>
	<div class="signup-container">
		<!-- Navigation Bar -->
		<div class="nav-bar">
			<button class="back-button" @click="goBack">←</button>
			<h1 class="nav-title">회원가입</h1>
		</div>

		<!-- Main Content -->
		<div class="main-content">
			<!-- Title Section -->
			<div class="title-section">
				<h2 class="signup-title">회원가입</h2>
				<p class="required-notice">* 필수 입력 항목</p>
			</div>

			<!-- Signup Form -->
			<div class="signup-form">
				<!-- Name Field -->
				<div class="field-group">
					<label class="field-label">이름 *</label>
					<input 
						type="text" 
						placeholder="이름을 입력하세요" 
						v-model="formData.full_name" 
						@blur="validateName"
						@input="handleNameInput"
						class="input-field" 
						:class="{ 'error': !nameValid && formData.full_name }"
						maxlength="18"
					/>
					<p class="field-help" :class="{ 'error-text': !nameValid && formData.full_name }">
						공백 없이 최대 18자까지 입력 가능
					</p>
				</div>

				<!-- Email + 인증번호 받기 -->
				<div class="field-group">
					<label class="field-label">이메일 *</label>
					<div class="input-with-button">
						<input 
							type="email" 
							placeholder="이메일을 입력하세요" 
							v-model="formData.email"
							@input="limitInput($event, 'email', 255)"
							class="input-field" 
							maxlength="50"
						/>
						<button type="button" class="duplicate-check-button" :disabled="!isValidEmail || emailSent" @click="sendCode">인증번호 받기</button>
						<span v-if="emailVerified" class="checkmark">✔</span>
					</div>
				</div>

				<!-- 인증번호 입력 & 확인 -->
				<div class="field-group" v-if="emailSent && !emailVerified">
					<label class="field-label">인증번호 입력</label>
					<div class="input-with-button">
						<input 
							type="text" 
							placeholder="인증번호 6자리" 
							v-model="code"
							@input="limitInput($event, 'code', 6)"
							class="input-field" 
							maxlength="6"
						/>
						<button type="button" class="duplicate-check-button" :disabled="!code" @click="verifyCode">인증번호 확인</button>
					</div>
				</div>

				<!-- Password Field -->
				<div class="field-group">
					<label class="field-label">비밀번호 *</label>
					<input 
						type="password" 
						placeholder="비밀번호를 입력하세요" 
						v-model="formData.password" 
						@blur="validatePassword"
						@input="limitInput($event, 'password', 20)"
						class="input-field" 
						:class="{ 'error': !passwordValid && formData.password }"
						maxlength="20"
					/>
					<p class="field-help" :class="{ 'error-text': !passwordValid && formData.password }">
						영문, 숫자, 특수문자 조합 8-20자리
					</p>
				</div>

				<!-- Password Confirm -->
				<div class="field-group">
					<label class="field-label">비밀번호 확인 *</label>
					<input 
						type="password" 
						placeholder="비밀번호를 다시 입력하세요" 
						v-model="formData.passwordConfirm" 
						@blur="validatePasswordConfirm"
						@input="limitInput($event, 'passwordConfirm', 20)"
						class="input-field" 
						:class="{ 'error': !passwordConfirmValid && formData.passwordConfirm }"
						maxlength="20"
					/>
				</div>

				<!-- Phone Field -->
				<div class="field-group">
					<label class="field-label">전화번호 *</label>
					<input 
						type="tel" 
						placeholder="전화번호를 입력하세요" 
						v-model="formData.phone"
						@input="handlePhoneInput"
						class="input-field" 
						maxlength="11"
					/>
					<p class="field-help">최대 11자까지 입력 가능 (숫자만 입력)</p>
				</div>

				<!-- Nickname + 중복확인 -->
				<div class="field-group">
					<label class="field-label">닉네임 *</label>
					<div class="input-with-button">
						<input 
							type="text" 
							placeholder="닉네임을 입력하세요" 
							v-model="formData.nickname"
							@input="limitInput($event, 'nickname', 18)"
							class="input-field" 
							maxlength="18"
						/>
						<button class="duplicate-check-button" @click="checkNickname">중복 확인</button>
						<span v-if="nickOK" class="checkmark">✔</span>
					</div>
					<p class="field-help">최대 18자까지 입력 가능</p>
				</div>

				<!-- Signup -->
				<button class="signup-button" :disabled="!canSignup" @click="handleSignup">
					<span class="button-text">회원가입</span>
				</button>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { defineComponent, reactive, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { BACKEND_BASE_URL } from "@/utils/api";

export default defineComponent({
	name: "Signup",
	setup() {
		const router = useRouter();
		const formData = reactive({
			full_name: "",
			email: "",
			password: "",
			passwordConfirm: "",
			phone: "",
			nickname: "",
		});

		/** 이메일 인증 */
		const emailSent = ref(false);
		const emailVerified = ref(false);
		const code = ref("");

		// 이메일 포맷 체크 (@ 포함 필수)
		const isValidEmail = computed(() => {
			const email = formData.email;
			return email.includes('@') && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
		});

		// 비밀번호 유효성 검사
		const checkNewPassword = (password: string) => {
			if (!password) {
				return true; // 빈 값은 required 검사에서 막음
			}

			// 1. 영문자(대소문자), 숫자, 특수문자 조합 8-20자리
			const validatePattern = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[$@$!%*#?&])[A-Za-z\d$@$!%*#?&]{8,20}$/;
			if (!validatePattern.test(password)) {
				alert('비밀번호는 영문자, 숫자, 특수문자 조합의 8~20자리를 사용해야 합니다.');
				return false;
			}

			// 2. 같은 문자 3개 이상 연속 체크 (예: aaa, 111)
			if (/(\w)\1\1/.test(password)) {
				alert('같은 문자를 3개 이상 사용할 수 없습니다.');
				return false;
			}

			// 3. 연속 문자/숫자 3개 이상 체크 (예: 123, 321, abc, cba)
			let cnt = 0;
			let cnt2 = 0;
			for (let i = 0; i < password.length - 2; i++) {
				const char1 = password.charAt(i);
				const char2 = password.charAt(i + 1);
				const char3 = password.charAt(i + 2);

				// 오름차순 연속 (123, abc)
				if (char1.charCodeAt(0) - char2.charCodeAt(0) === -1 && 
					char2.charCodeAt(0) - char3.charCodeAt(0) === -1) {
					cnt++;
				}
				// 내림차순 연속 (321, cba)
				if (char1.charCodeAt(0) - char2.charCodeAt(0) === 1 && 
					char2.charCodeAt(0) - char3.charCodeAt(0) === 1) {
					cnt2++;
				}
			}

			if (cnt > 0 || cnt2 > 0) {
				alert('연속된 문자를 3개 이상 사용하실 수 없습니다.\n(ex: 123, 321, abc, cba 포함 불가)');
				return false;
			}

			return true;
		};

		// 비밀번호 유효성 상태
		const passwordValid = ref(true);
		const passwordConfirmValid = ref(true);

		// 이름 유효성 상태
		const nameValid = ref(true);

		// 비밀번호 유효성 검사 함수 호출
		const validatePassword = () => {
			passwordValid.value = checkNewPassword(formData.password);
		};

		// 비밀번호 확인 유효성 검사
		const validatePasswordConfirm = () => {
			// 정규식 검사와 비밀번호 일치 검사
			const isValidFormat = checkNewPassword(formData.passwordConfirm);
			const isMatching = formData.password === formData.passwordConfirm;
			
			if (!isValidFormat) {
				passwordConfirmValid.value = false;
			} else if (!isMatching) {
				alert('비밀번호가 일치하지 않습니다.');
				passwordConfirmValid.value = false;
			} else {
				passwordConfirmValid.value = true;
			}
		};

		// 이름 유효성 검사
		const validateName = () => {
			if (formData.full_name.includes(' ')) {
				alert('이름에는 공백을 포함할 수 없습니다.');
				nameValid.value = false;
			} else {
				nameValid.value = true;
			}
		};

		// 이름 입력 시 공백 제거
		const handleNameInput = () => {
			formData.full_name = formData.full_name.replace(/\s/g, '');
		};

		// 전화번호 입력 시 숫자만 허용
		const handlePhoneInput = (event: Event) => {
			const target = event.target as HTMLInputElement;
			const value = target.value;
			// 숫자가 아닌 문자 제거
			const numericValue = value.replace(/[^0-9]/g, '');
			// 최대 11자로 제한
			if (numericValue.length > 11) {
				formData.phone = numericValue.substring(0, 11);
			} else {
				formData.phone = numericValue;
			}
		};

		// 입력 길이 제한 함수
		const limitInput = (event: Event, field: string, maxLength: number) => {
			const target = event.target as HTMLInputElement;
			const value = target.value;
			
			if (field === 'full_name') {
				// 이름은 공백 제거 후 길이 체크
				const cleanValue = value.replace(/\s/g, '');
				if (cleanValue.length > maxLength) {
					formData.full_name = cleanValue.substring(0, maxLength);
				} else {
					formData.full_name = cleanValue;
				}
			} else {
				// 다른 필드들은 일반적인 길이 제한
				if (value.length > maxLength) {
					target.value = value.substring(0, maxLength);
					// reactive 객체 업데이트
					switch (field) {
						case 'email':
							formData.email = target.value;
							break;
						case 'password':
							formData.password = target.value;
							break;
						case 'passwordConfirm':
							formData.passwordConfirm = target.value;
							break;
						case 'phone':
							formData.phone = target.value;
							break;
						case 'nickname':
							formData.nickname = target.value;
							break;
						case 'code':
							code.value = target.value;
							break;
					}
				}
			}
		};

		// 중복확인 상태
		const nickOK = ref(false);

		// 인증번호 발송
		const sendCode = async () => {
			// 이메일 유효성 검사
			if (!formData.email) {
				alert("이메일을 입력해주세요.");
				return;
			}
			
			if (!formData.email.includes('@')) {
				alert("이메일 주소에 @가 포함되어야 합니다.");
				return;
			}
			
			if (!isValidEmail.value) {
				alert("유효한 이메일 형식을 입력해주세요.");
				return;
			}

			// 1) 이메일 중복 확인
			try {
				const dupRes = await fetch(`${BACKEND_BASE_URL}/auth/check-email/?email=${encodeURIComponent(formData.email)}`);
				const dupJson = await dupRes.json();
				if (!dupRes.ok || dupJson.exists) {
					alert("이미 사용 중인 이메일입니다.");
					return;
				}
			} catch {
				alert("이메일 중복체크에 실패했습니다.");
				return;
			}

			// 2) 중복 없으면 인증번호 발송
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/request/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ email: formData.email }),
				});
				if (!res.ok) throw new Error();
				emailSent.value = true;
				alert("인증번호를 발송했습니다.");
			} catch {
				alert("인증번호 발송 실패");
			}
		};

		// 인증번호 확인
		const verifyCode = async () => {
			if (!code.value) return;
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/verify/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ email: formData.email, code: code.value }),
				});
				if (!res.ok) {
					const { detail } = await res.json();
					throw new Error(detail || "인증 실패");
				}
				emailVerified.value = true;
				alert("이메일 인증이 완료되었습니다.");
			} catch (err: any) {
				alert(err.message);
			}
		};

		// 닉네임 중복확인
		const checkNickname = async () => {
			console.log("[중복체크] nickname:", formData.nickname);
			if (!formData.nickname) {
				return alert("닉네임을 입력해주세요.");
			}
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/check-nickname/?nickname=${encodeURIComponent(formData.nickname)}`);
				const json = await res.json();
				console.log("Nickname check response:", json);
				if (res.ok && !json.exists) {
					nickOK.value = true;
				} else {
					alert("이미 사용 중인 닉네임입니다.");
					nickOK.value = false;
				}
			} catch {
				alert("닉네임 중복체크 실패");
			}
		};

		// 최종 회원가입 버튼 활성화 여부
		const canSignup = computed(() => {
			return (
				emailVerified.value &&
				nickOK.value &&
				formData.full_name.trim().length > 0 &&
				formData.password &&
				passwordValid.value &&
				passwordConfirmValid.value &&
				formData.password === formData.passwordConfirm &&
				formData.phone.trim().length > 0 &&
				formData.nickname.trim().length > 0
			);
		});

		// 회원가입 API 호출
		const handleSignup = async () => {
			// 비밀번호 유효성 재검사
			if (!checkNewPassword(formData.password)) {
				return;
			}
			if (formData.password !== formData.passwordConfirm) {
				return alert("비밀번호가 일치하지 않습니다.");
			}
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/signup/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						full_name: formData.full_name,
						email: formData.email,
						password: formData.password,
						password2: formData.passwordConfirm,
						phone: formData.phone,
						nickname: formData.nickname,
					}),
				});
				const data = await res.json();
				if (res.ok) {
					// 성공 시 backend의 message 또는 detail 중 있는 걸 쓰고
					const msg = data.message || data.detail || "회원가입 성공!";
					alert(msg);
					router.push("/login");
				} else {
					// 에러 키들을 합쳐서 보여주기
					if (data.detail) {
						alert("회원가입 실패: " + data.detail);
					} else {
						// field별 에러 메시지를 모두 문자열로 합치기
						const msgs = Object.values(data).flat().join("\n");
						alert("회원가입 실패:\n" + msgs);
					}
				}
			} catch {
				alert("회원가입 요청 중 네트워크 오류가 발생했습니다.");
			}
		};

		return {
			formData,
			emailSent,
			emailVerified,
			code,
			isValidEmail,
			sendCode,
			verifyCode,
			nickOK,
			checkNickname,
			canSignup,
			handleSignup,
			passwordValid,
			passwordConfirmValid,
			nameValid,
			validatePassword,
			validatePasswordConfirm,
			validateName,
			handleNameInput,
			handlePhoneInput,
			limitInput,
			goBack: () => router.back(),
		};
	},
});
</script>

<style scoped>
.signup-container {
	width: 100%;
	min-height: 100vh;
	background-color: #f3eeea;
	position: relative;
	overflow-x: hidden;
	font-family: "Inter", sans-serif;
	display: flex;
	flex-direction: column;
	align-items: center;
}

/* Navigation Bar */
.nav-bar {
	width: 100%;
	max-width: 440px;
	height: 56px;
	background-color: #ffffff;
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0 16px;
	position: sticky;
	top: 0;
	z-index: 10;
}

.back-button {
	background: none;
	border: none;
	font-size: 24px;
	color: #333333;
	cursor: pointer;
	padding: 8px;
}

.nav-title {
	font-size: 18px;
	font-weight: 600;
	color: #333333;
	margin: 0;
}

/* Main Content */
.main-content {
	width: 100%;
	max-width: 440px;
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
}

/* Title Section */
.title-section {
	margin-top: 20px;
	margin-bottom: 30px;
	width: 100%;
	max-width: 344px;
	padding: 0 48px;
}

.signup-title {
	font-size: 30px;
	font-weight: 600;
	color: #000000;
	margin: 0 0 10px 0;
	line-height: 36px;
}

.required-notice {
	font-size: 12px;
	color: #cc3333;
	margin: 0;
	line-height: 14px;
}

/* Signup Form */
.signup-form {
	width: 100%;
	max-width: 344px;
	display: flex;
	flex-direction: column;
	gap: 25px;
	padding: 0 48px 100px 48px;
}

.field-group {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.field-label {
	font-size: 16px;
	font-weight: 600;
	color: #333333;
	margin: 0;
	line-height: 19px;
}

.input-field {
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

.input-field::placeholder {
	color: #999999;
}

.input-field:focus {
	border-color: #776b5d;
}

.input-field.error {
	border-color: #cc3333;
	background-color: #fff5f5;
}

.input-with-button {
	display: flex;
	gap: 8px;
	align-items: center;
}

.input-with-button .input-field {
	flex: 1;
}

.duplicate-check-button {
	height: 27px;
	background-color: #776b5d;
	border: none;
	border-radius: 4px;
	color: #ffffff;
	font-size: 12px;
	font-weight: 600;
	padding: 0 12px;
	cursor: pointer;
	white-space: nowrap;
	flex-shrink: 0;
}

.field-help {
	font-size: 12px;
	color: #999999;
	margin: 0;
	line-height: 14px;
}

.field-help.error-text {
	color: #cc3333;
}

/* Signup Button */
.signup-button {
	width: 100%;
	height: 50px;
	background-color: #776b5d;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: none; /* 호버 애니메이션 제거 */
	display: flex;
	align-items: center;
	justify-content: center;
	margin-top: 20px;
}

.signup-button:hover {
	background-color: #665a4d;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
}
/* 비활성화된 상태일 때 */
.signup-button:disabled {
	background-color: #cccccc; /* 회색 */
	cursor: not-allowed;
}

/* :disabled 상태에선 hover 스타일 무시 */
.signup-button:disabled:hover {
	transform: none;
	box-shadow: none;
}
.button-text {
	color: #ffffff;
	font-family: "Inter", sans-serif;
	font-weight: 600;
	font-size: 16px;
	line-height: 19px;
	letter-spacing: 0;
}

.link {
	color: #808080;
	text-decoration: none;
	font-size: 14px;
	font-weight: 400;
	line-height: 16.94px;
	transition: color 0.3s ease;
}

/* Responsive Design */
@media (max-width: 440px) {
	.title-section {
		padding: 0 20px;
	}

	.signup-form {
		padding: 0 20px 100px 20px;
	}

	.signup-container {
		width: 100vw;
	}
}

@media (min-width: 441px) {
	.signup-container {
		width: 440px;
		margin: 0 auto;
	}
}
</style>
