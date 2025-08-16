<template>
	<div class="forgot-password-container">
		<div class="main-content">
			<div class="title-section">
				<h1 class="forgot-password-title">비밀번호 찾기</h1>
			</div>

			<div class="forgot-password-form">
				<!-- 이름 및 이메일 입력 -->
				<div class="field-group">
					<label class="field-label">이름</label>
					<input type="text" v-model="form.name" placeholder="이름 입력" class="input-field" :disabled="step !== 'request'" />

					<label class="field-label">이메일</label>
					<input type="email" v-model="form.email" placeholder="이메일 입력" class="input-field" :disabled="step !== 'request'" />

					<button class="send-verification-button" @click="sendCode" :disabled="!canSendCode">
						<span class="button-text">인증번호 발송</span>
					</button>
				</div>

				<!-- 인증번호 입력 -->
				<div class="field-group">
					<label class="field-label">인증번호 입력</label>
					<div class="input-with-button">
						<input type="text" v-model="form.code" placeholder="인증번호 입력" class="input-field" :disabled="step === 'request'" />
						<button class="verify-button" @click="verifyCode" :disabled="!canVerify">확인</button>
					</div>
				</div>

				<!-- 새 비밀번호 입력 -->
				<div class="field-group">
					<label class="field-label">새 비밀번호 입력</label>
					<input type="password" v-model="form.newPassword" placeholder="비밀번호 입력" class="input-field" :disabled="step !== 'reset'" />
					<p class="field-help">영문, 숫자, 특수문자 조합 8-20자리</p>
				</div>

				<div class="field-group">
					<label class="field-label">새 비밀번호 확인</label>
					<input type="password" v-model="form.newPasswordConfirm" placeholder="비밀번호 입력" class="input-field" :disabled="step !== 'reset'" />
					<p class="field-help">위와 동일한 비밀번호를 다시 입력해주세요</p>
				</div>

				<button class="change-password-button" @click="changePassword" :disabled="!canChange">
					<span class="button-text">비밀번호 변경 완료</span>
				</button>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { defineComponent, reactive, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { BACKEND_BASE_URL } from "@/utils/api";
import { alert, alertSuccess, alertWarning, alertError } from "@/composables/useAlert";

export default defineComponent({
	name: "ForgotPassword",
	setup() {
		const router = useRouter();
		const step = ref<"request" | "verify" | "reset">("request");
		const form = reactive({
			name: "",
			email: "",
			code: "",
			newPassword: "",
			newPasswordConfirm: "",
		});

		// 1단계: 이름·이메일이 올바르면 활성화
		const canSendCode = computed(() => step.value === "request" && form.name.trim() !== "" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email));
		// 2단계: 코드가 입력되면 활성화
		const canVerify = computed(() => step.value === "verify" && form.code.trim() !== "");
		// 3단계: 새 비밀번호가 조건 충족 시 활성화
		const canChange = computed(() => step.value === "reset" && form.newPassword.length >= 8 && form.newPassword === form.newPasswordConfirm);

		const sendCode = async () => {
			if (!canSendCode.value) return;
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/password-reset/request/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ name: form.name, email: form.email }),
				});
				const json = await res.json();
				if (res.ok) {
					await alertSuccess("인증번호를 이메일로 전송했습니다.");
					step.value = "verify";
				} else {
					await alertError(json.detail || "인증번호 발송 실패");
				}
			} catch {
				await alertError("네트워크 오류");
			}
		};

		const verifyCode = async () => {
			if (!canVerify.value) return;
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/password-reset/verify/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ email: form.email, code: form.code }),
				});
				const json = await res.json();
				if (res.ok) {
					await alertSuccess("인증번호 확인 완료");
					step.value = "reset";
				} else {
					await alertError(json.detail || "인증번호 불일치");
				}
			} catch {
				await alertError("네트워크 오류");
			}
		};

		const changePassword = async () => {
			if (!canChange.value) return;
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/auth/password-reset/confirm/`, {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						email: form.email,
						code: form.code,
						new_password: form.newPassword,
						new_password2: form.newPasswordConfirm,
					}),
				});
				const json = await res.json();
				if (res.ok) {
					await alertSuccess("비밀번호 변경 완료");
					router.push("/login");
				} else {
					await alertError(json.detail || "변경 실패");
				}
			} catch {
				await alertError("네트워크 오류");
			}
		};

		return {
			form,
			step,
			canSendCode,
			canVerify,
			canChange,
			sendCode,
			verifyCode,
			changePassword,
		};
	},
});
</script>

<style scoped>
.forgot-password-container {
	width: 100%;
	min-height: 100vh;
	background-color: #F9F5EC;
	position: relative;
	overflow-x: hidden;
	font-family: "Inter", sans-serif;
	display: flex;
	flex-direction: column;
	align-items: center;
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
	margin-top: 60px;
	margin-bottom: 40px;
	width: 100%;
	max-width: 344px;
	padding: 0 48px;
}

.forgot-password-title {
	font-size: 24px;
	font-weight: 700;
	color: #000000;
	margin: 0;
	line-height: 22px;
}

/* Forgot Password Form */
.forgot-password-form {
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
	border-color: #4B3D34;
}

.input-with-button {
	display: flex;
	gap: 8px;
	align-items: center;
}

.input-with-button .input-field {
	flex: 1;
}
/* 비활성화된 input 스타일 */
.input-field:disabled {
	background-color: #e0e0e0;
	border-color: #cccccc;
	cursor: not-allowed;
}

/* 비활성화된 버튼 스타일 */
button:disabled {
	background-color: #cccccc;
	cursor: not-allowed;
	box-shadow: none;
}

/* 버튼 호버링: 활성화된 버튼만 */
.send-verification-button:not(:disabled):hover,
.change-password-button:not(:disabled):hover {
	background-color: #594D44;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(75, 61, 52, 0.3);
}

.verify-button:not(:disabled):hover {
	background-color: #594D44;
}
.verify-button {
	height: 30px;
	background-color: #4B3D34;
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

/* Buttons */
.send-verification-button,
.change-password-button {
	width: 100%;
	height: 50px;
	background-color: #4B3D34;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.3s ease;
	display: flex;
	align-items: center;
	justify-content: center;
}

.send-verification-button:hover,
.change-password-button:hover {
	background-color: #594D44;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(75, 61, 52, 0.3);
}

.button-text {
	color: #ffffff;
	font-family: "Inter", sans-serif;
	font-weight: 600;
	font-size: 16px;
	line-height: 19px;
	letter-spacing: 0;
}

/* Responsive Design */
@media (max-width: 440px) {
	.title-section {
		padding: 0 20px;
	}

	.forgot-password-form {
		padding: 0 20px 100px 20px;
	}

	.forgot-password-container {
		width: 100vw;
	}
}

@media (min-width: 441px) {
	.forgot-password-container {
		width: 440px;
		margin: 0 auto;
	}
}
</style>
