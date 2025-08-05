<template>
	<div class="login-container">
		<!-- Main Content -->
		<div class="main-content">
			<!-- Logo -->
			<div class="logo-container">
				<div class="logo-image"></div>
			</div>

			<!-- Login Form -->
			<div class="login-form">
				<!-- Email Input -->
				<div class="input-field">
					<input type="email" placeholder="이메일 입력" v-model="email" class="input" />
				</div>

				<!-- Password Input -->
				<div class="input-field">
					<input type="password" placeholder="비밀번호 입력" v-model="password" class="input" />
				</div>

				<!-- Login Button -->
				<button class="login-button" @click="handleLogin">
					<span class="button-text">로그인</span>
				</button>

				<!-- Social Login Buttons -->
				<div class="social-login">
					<!-- Google Login -->
					<button class="google-login-button" @click="handleGoogleLogin">
						<div class="google-icon"></div>
						<span class="button-text">구글 로그인</span>
					</button>

					<!-- Kakao Login -->
					<button class="kakao-login-button" @click="handleKakaoLogin">
						<span class="button-text">카카오 로그인</span>
					</button>
				</div>

				<!-- Links -->
				<div class="links">
					<router-link to="/signup" class="link">회원가입</router-link>
					<span class="separator">|</span>
					<router-link to="/forgot-password" class="link">비밀번호 찾기</router-link>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { defineComponent, ref } from "vue";
import { useRouter } from "vue-router";
import { BACKEND_BASE_URL } from "@/utils/api";
import { useUserStore } from "@/stores/user";

export default defineComponent({
	name: "Login",
	setup() {
		const router = useRouter();
		const email = ref("");
		const password = ref("");

		const handleLogin = async () => {
			if (!email.value || !password.value) {
				return alert("이메일과 비밀번호를 모두 입력해주세요.");
			}

			try {
				const userStore = useUserStore();
				// 기본 login 함수 사용 (api.ts에서 fallback URL 처리)
				await userStore.login(email.value, password.value);
				router.push("/main");
			} catch (err: any) {
				console.error("로그인 실패:", err);
				alert("로그인 실패: " + err.message);
			}
		};

		const handleGoogleLogin = () => {
			const backendUrl = BACKEND_BASE_URL || "https://i13e102.p.ssafy.io/api";
			window.location.href = `${backendUrl}/auth/social/google/login/`;
		};

		const handleKakaoLogin = () => {
			console.log("카카오 로그인 시도");
			router.push("/social-login-info");
		};

		return {
			email,
			password,
			handleLogin,
			handleGoogleLogin,
			handleKakaoLogin,
		};
	},
});
</script>

<style scoped>
.login-container {
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

.main-content {
	width: 100%;
	max-width: 440px;
	min-height: 100vh;
	display: flex;
	flex-direction: column;
	align-items: center;
	position: relative;
}

/* Logo */
.logo-container {
	margin-top: 113px;
	width: 200px;
	height: 31px;
	display: flex;
	justify-content: center;
	align-items: center;
	margin-bottom: 60px;
}

.logo-image {
	width: 100%;
	height: 100%;
	background-image: url("@/assets/alpaca-logo.png");
	background-size: contain;
	background-position: center;
	background-repeat: no-repeat;
}

/* Login Form */
.login-form {
	width: 100%;
	max-width: 344px;
	display: flex;
	flex-direction: column;
	gap: 20px;
	flex: 1;
	padding: 0 48px;
}

.input-field {
	width: 100%;
}

.input {
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

.input::placeholder {
	color: #999999;
}

.input:focus {
	border-color: #776b5d;
}

/* Login Button */
.login-button {
	width: 100%;
	height: 50px;
	background-color: #776b5d;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.3s ease;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 20px;
}

.login-button:hover {
	background-color: #665a4d;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
}

/* Social Login */
.social-login {
	display: flex;
	flex-direction: column;
	gap: 16px;
	margin-bottom: 30px;
}

.google-login-button {
	width: 100%;
	height: 50px;
	background-color: #f5f5f5;
	border: 1px solid #cccccc;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.3s ease;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12px;
}

.google-login-button:hover {
	background-color: #e8e8e8;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.google-icon {
	width: 24px;
	height: 24px;
	background-image: url("@/assets/google-login.png");
	background-size: contain;
	background-position: center;
	background-repeat: no-repeat;
	flex-shrink: 0;
}

.kakao-login-button {
	width: 100%;
	height: 50px;
	background-color: #f9e000;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.3s ease;
	display: flex;
	align-items: center;
	justify-content: center;
}

.kakao-login-button:hover {
	background-color: #f0d800;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(249, 224, 0, 0.3);
}

.button-text {
	font-family: "Inter", sans-serif;
	font-weight: 600;
	font-size: 16px;
	line-height: 19.36px;
	letter-spacing: 0;
}

.login-button .button-text {
	color: #ffffff;
}

.google-login-button .button-text,
.kakao-login-button .button-text {
	color: #333333;
}

/* Links */
.links {
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 10px;
	margin-top: 20px;
	margin-bottom: 50px;
}

.link {
	color: #808080;
	text-decoration: none;
	font-size: 14px;
	font-weight: 400;
	line-height: 16.94px;
	transition: color 0.3s ease;
}

.link:hover {
	color: #666666;
}

.separator {
	color: #808080;
	font-size: 14px;
}

/* Responsive Design */
@media (max-width: 440px) {
	.login-form {
		padding: 0 20px;
	}

	.login-container {
		width: 100vw;
	}
}

@media (min-width: 441px) {
	.login-container {
		width: 440px;
		margin: 0 auto;
	}
}
</style>