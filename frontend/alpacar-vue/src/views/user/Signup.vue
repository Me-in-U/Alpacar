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
					<input v-model="formData.full_name" @input="handleNameInput" @keypress="preventInvalidNameChars" :class="['input-field', { error: formData.full_name && !nameValid }]" placeholder="이름을 입력하세요" maxlength="18" />
					<p v-if="formData.full_name && !nameValid" class="field-help error-text">한글/영문만 1~18자</p>
				</div>

				<!-- Email + 인증번호 받기 -->
				<div class="field-group">
					<label class="field-label">이메일 *</label>
					<div class="input-with-button">
						<input v-model="formData.email" @input="emailVerified = false" :class="['input-field', { error: formData.email && !emailFormatValid }]" placeholder="이메일을 입력하세요" maxlength="50" />
						<button class="duplicate-check-button" :disabled="!emailFormatValid || emailSent" @click="sendCode">인증번호 받기</button>
						<span v-if="emailVerified" class="checkmark">✔</span>
					</div>
					<p v-if="formData.email && !emailFormatValid" class="field-help error-text">올바른 이메일 형식이 아닙니다.</p>
				</div>

				<!-- 인증번호 입력 & 확인 -->
				<div class="field-group" v-if="emailSent && !emailVerified">
					<label class="field-label">인증번호 입력</label>
					<div class="input-with-button">
						<input v-model="formData.code" placeholder="인증번호 6자리" maxlength="6" class="input-field" />
						<button class="duplicate-check-button" :disabled="!formData.code" @click="verifyCode">확인</button>
					</div>
				</div>

				<!-- Password Field -->
				<div class="field-group">
					<label class="field-label">비밀번호 *</label>
					<input type="password" v-model="formData.password" :class="['input-field', { error: formData.password && !passwordValid }]" placeholder="비밀번호를 입력하세요" maxlength="20" />
					<ul v-if="formData.password && !passwordValid" class="password-rules">
						<li :class="lengthValid ? 'valid' : 'invalid'">8~20자</li>
						<li :class="letterValid ? 'valid' : 'invalid'">문자 포함</li>
						<li :class="numberValid ? 'valid' : 'invalid'">숫자 포함</li>
						<li :class="specialValid ? 'valid' : 'invalid'">특수문자 포함</li>
						<li :class="noTripleValid ? 'valid' : 'invalid'">동일문자 3연속 불가</li>
						<li :class="noSeqValid ? 'valid' : 'invalid'">연속문자 3연속 불가</li>
					</ul>
				</div>

				<!-- Password Confirm -->
				<div class="field-group">
					<label class="field-label">비밀번호 확인 *</label>
					<input
						type="password"
						v-model="formData.passwordConfirm"
						:class="['input-field', { error: formData.passwordConfirm && !passwordConfirmValid }]"
						placeholder="비밀번호를 다시 입력하세요"
						maxlength="20"
					/>
					<p v-if="formData.passwordConfirm" :class="['field-help', passwordConfirmValid ? '' : 'error-text']">
						{{ passwordConfirmValid ? "일치합니다." : "일치하지 않습니다." }}
					</p>
				</div>

				<!-- Phone Field -->
				<div class="field-group">
					<label class="field-label">전화번호 *</label>

					<input v-model="formData.phoneDisplay" @input="onPhoneInput" @keypress="preventInvalidPhoneChars" :class="['input-field', { error: formData.phone && !phoneValid }]" placeholder="ex) 010-1234-1234" maxlength="13" />
					<p v-if="formData.phone && !phoneValid" class="field-help error-text">숫자만, 최대 11자</p>
				</div>

				<!-- Nickname + 중복확인 -->
				<div class="field-group">
					<label class="field-label">닉네임 *</label>
					<div class="input-with-button">
						<input v-model="formData.nickname" @input="handleNicknameInput" @keypress="preventInvalidNicknameChars" :class="['input-field', { error: formData.nickname && !nicknameValid }]" placeholder="닉네임을 입력하세요" maxlength="18" />
						<button class="duplicate-check-button" @click="checkNickname">중복확인</button>
						<span v-if="nickOK" class="checkmark">✔</span>
					</div>
					<p v-if="formData.nickname && !nicknameValid" class="field-help error-text">특수문자 금지, 1~18자, 중복확인 필요</p>
				</div>

				<!-- Signup Button -->
				<button class="signup-button" :disabled="!canSignup" @click="handleSignup">회원가입</button>
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
			code: "",
			password: "",
			passwordConfirm: "",
			phoneDisplay: "",
			phone: "",
			nickname: "",
		});

		const emailSent = ref(false);
		const emailVerified = ref(false);
		const nickOK = ref(false);

		// 1) 이름 유효성 - 한글, 영문만 허용
		const nameValid = computed(() => {
			const koreanEnglishOnly = /^[a-zA-Z가-힣]+$/.test(formData.full_name);
			return formData.full_name.length > 0 && formData.full_name.length <= 18 && koreanEnglishOnly;
		});
		const handleNameInput = () => {
			// 공백 제거 및 한글/영문만 유지
			formData.full_name = formData.full_name.replace(/[^a-zA-Z가-힣]/g, "");
		};
		const preventInvalidNameChars = (e: KeyboardEvent) => {
			const char = e.key;
			// 한글, 영문, 백스페이스, 방향키 등 허용
			if (!/[a-zA-Z가-힣]/.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(char)) {
				e.preventDefault();
			}
		};

		// 2) 이메일 형식
		const emailFormatValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email));

		// 비밀번호 규칙
		// 1) 길이 유효성
		const lengthValid = computed(() => formData.password.length >= 8 && formData.password.length <= 20);

		// 2) 문자 포함
		const letterValid = computed(() => /[a-zA-Z]/.test(formData.password));

		// 3) 숫자 포함
		const numberValid = computed(() => /\d/.test(formData.password));

		// 4) 특수문자 포함
		const specialValid = computed(() => /[$@!%*#?&/]/.test(formData.password));

		// 5) 동일문자 3연속 금지
		const noTripleValid = computed(() => !/(\w)\1\1/.test(formData.password));

		// 6) 연속문자 3연속 금지
		const noSeqValid = computed(() => {
			for (let i = 0; i < formData.password.length - 2; i++) {
				const a = formData.password.charCodeAt(i),
					b = formData.password.charCodeAt(i + 1),
					c = formData.password.charCodeAt(i + 2);
				if ((b === a + 1 && c === b + 1) || (b === a - 1 && c === b - 1)) {
					return false;
				}
			}
			return true;
		});

		// 최종 전체 유효성
		const passwordValid = computed(() => [lengthValid, letterValid, numberValid, specialValid, noTripleValid, noSeqValid].every((v) => v.value));

		// 4) 비밀번호 확인
		const passwordConfirmValid = computed(() => formData.passwordConfirm === formData.password && formData.passwordConfirm.length > 0);

		// 5) 전화번호 - 숫자만 허용
		const phoneValid = computed(() => /^[0-9]{1,11}$/.test(formData.phone));
		const onPhoneInput = (e: Event) => {
			// 입력값에서 숫자만 추출
			let digits = (e.target as HTMLInputElement).value.replace(/[^0-9]/g, "");
			if (digits.length > 11) digits = digits.slice(0, 11);
			// 화면용: 3-4-4 포맷
			const part1 = digits.slice(0, 3);
			const part2 = digits.length >= 4 ? digits.slice(3, 7) : "";
			const part3 = digits.length >= 8 ? digits.slice(7) : "";
			formData.phoneDisplay = [part1, part2, part3].filter(Boolean).join("-");
			// 실제 전송용: 숫자만
			formData.phone = digits;
		};
		const preventInvalidPhoneChars = (e: KeyboardEvent) => {
			const char = e.key;
			// 숫자, 백스페이스, 방향키 등만 허용
			if (!/[0-9]/.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(char)) {
				e.preventDefault();
			}
		};

		// 6) 닉네임 - 특수문자 금지 (한글, 영문, 숫자만 허용)
		const nicknameValid = computed(() => {
			const noSpecialChars = /^[a-zA-Z가-힣0-9]+$/.test(formData.nickname);
			return formData.nickname.length > 0 && formData.nickname.length <= 18 && noSpecialChars && nickOK.value;
		});
		const handleNicknameInput = () => {
			// 특수문자 제거 및 한글/영문/숫자만 유지
			formData.nickname = formData.nickname.replace(/[^a-zA-Z가-힣0-9]/g, "");
			nickOK.value = false;
		};
		const preventInvalidNicknameChars = (e: KeyboardEvent) => {
			const char = e.key;
			// 한글, 영문, 숫자, 백스페이스, 방향키 등 허용
			if (!/[a-zA-Z가-힣0-9]/.test(char) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(char)) {
				e.preventDefault();
			}
		};

		// 7) 전체 가입 가능
		const canSignup = computed(() => nameValid.value && emailFormatValid.value && emailVerified.value && passwordValid.value && passwordConfirmValid.value && phoneValid.value && nicknameValid.value);

		// 이메일 인증번호 발송
		const sendCode = async () => {
			try {
				// 중복체크
				const dup = await fetch(`${BACKEND_BASE_URL}/auth/check-email/?email=${encodeURIComponent(formData.email)}`);
				const { exists } = await dup.json();
				if (exists) return alert("이미 사용 중인 이메일입니다.");
				// 발송
				await fetch(`${BACKEND_BASE_URL}/auth/email-verify/request/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ email: formData.email }),
				});
				emailSent.value = true;
				alert("인증번호를 발송했습니다.");
			} catch {
				alert("인증번호 발송 실패");
			}
		};

		// 인증번호 확인
		const verifyCode = async () => {
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/verify/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ email: formData.email, code: formData.code }),
				});
				if (!res.ok) throw await res.json();
				emailVerified.value = true;
				alert("이메일 인증이 완료되었습니다.");
			} catch (err: any) {
				alert(err.detail || "인증 실패");
			}
		};

		// 닉네임 중복확인
		const checkNickname = async () => {
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/check-nickname/?nickname=${encodeURIComponent(formData.nickname)}`);
				const { exists } = await res.json();
				if (exists) return alert("이미 사용 중인 닉네임입니다.");
				nickOK.value = true;
			} catch {
				alert("중복확인 실패");
			}
		};
		// 자동 로그인 처리 함수
		const performAutoLogin = async () => {
			try {
				const loginRes = await fetch(`${BACKEND_BASE_URL}/auth/login/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						email: formData.email,
						password: formData.password,
					}),
				});

				const loginData = await loginRes.json();

				if (loginRes.ok && loginData.access) {
					// 토큰 저장
					localStorage.setItem("access_token", loginData.access);
					if (loginData.refresh) {
						localStorage.setItem("refresh_token", loginData.refresh);
					}

					// 사용자 정보 저장 (있는 경우)
					if (loginData.user) {
						localStorage.setItem("user", JSON.stringify(loginData.user));
					}

					console.log("자동 로그인 성공");
					router.push("/social-login-info");
				} else {
					console.error("자동 로그인 실패:", loginData);
					alert("회원가입은 완료되었지만 로그인에 실패했습니다. 로그인 페이지에서 다시 시도해주세요.");
					router.push("/login");
				}
			} catch (error) {
				console.error("자동 로그인 중 오류:", error);
				alert("회원가입은 완료되었지만 로그인에 실패했습니다. 로그인 페이지에서 다시 시도해주세요.");
				router.push("/login");
				alert("중복확인 실패");
			}
		};
		// 회원가입 요청
		const handleSignup = async () => {
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

					// 회원가입 성공 후 자동 로그인 처리
					await performAutoLogin();
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

		const goBack = () => router.back();

		return {
			formData,
			emailSent,
			emailVerified,
			nickOK,

			nameValid,
			emailFormatValid,

			// 여기 추가
			lengthValid,
			letterValid,
			numberValid,
			specialValid,
			noTripleValid,
			noSeqValid,

			passwordValid,
			passwordConfirmValid,
			phoneValid,
			nicknameValid,
			canSignup,

			handleNameInput,
			preventInvalidNameChars,
			onPhoneInput,
			preventInvalidPhoneChars,
			handleNicknameInput,
			preventInvalidNicknameChars,
			sendCode,
			verifyCode,
			checkNickname,
			handleSignup,
			goBack,
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
/* 비밀번호 조건 메시지 색상 */
.password-rules li {
	line-height: 1.4;
	/* 기본 회색으로 두고 */
	color: #999;
}
.password-rules li.valid {
	color: #4caf50; /* 초록 */
}
.password-rules li.invalid {
	color: #f44336; /* 빨강 */
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
