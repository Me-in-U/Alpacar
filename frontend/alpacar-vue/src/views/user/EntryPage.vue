<template>
	<div class="entry-page-container">
		<!-- Background Image (항상 표시) -->
		<div class="background-image"></div>

		<!-- Logo Container -->
		<div class="logo-container">
			<div class="logo-image" :class="{ 'logo-animate': logoAnimated }"></div>
		</div>

		<!-- Buttons Container -->
		<div class="buttons-container" :class="{ 'buttons-fade-in': buttonsVisible }">
			<button class="login-button" @click="goToLogin">
				<span class="button-text">로그인</span>
			</button>
			<button class="signup-button" @click="goToSignup">
				<span class="button-text">회원가입</span>
			</button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const logoAnimated = ref(false);
const buttonsVisible = ref(false);

const goToLogin = () => {
	router.push("/login");
};

const goToSignup = () => {
	router.push("/signup");
};

onMounted(() => {
	// 로고 애니메이션 시작 (100ms 후)
	setTimeout(() => {
		logoAnimated.value = true;
	}, 100);

	// 로고 애니메이션 완료 후 버튼 페이드인 (2.6초 후)
	setTimeout(() => {
		buttonsVisible.value = true;
	}, 2600);
});
</script>

<style scoped>
.entry-page-container {
	width: 440px;
	height: 956px;
	position: relative;
	overflow: hidden;
	font-family: "Inter", sans-serif;
	margin: 0 auto;
}

.background-image {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background-image: url("@/assets/background-banner.png");
	background-size: cover;
	background-position: center;
	background-repeat: no-repeat;
	z-index: 1;
}

/* Logo Container */
.logo-container {
	position: absolute;
	left: 50%;
	width: 380px;
	height: 59px;
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 5;
	top: 50%;
	transform: translateX(-50%) translateY(-50%);
}

.logo-image {
	width: 100%;
	height: 100%;
	background-image: url("@/assets/alpaca-logo.png");
	background-size: contain;
	background-position: center;
	background-repeat: no-repeat;
	transition: all 2.5s ease;
}

.logo-image.logo-animate {
	transform: translateY(-300px);
}

/* Buttons Container */
.buttons-container {
	position: absolute;
	bottom: 150px;
	left: 50%;
	transform: translateX(-50%) translateY(30px);
	width: 344px;
	display: flex;
	flex-direction: column;
	gap: 40px;
	z-index: 5;
	opacity: 0;
	transition: all 0.5s ease;
	align-items: center;
	justify-content: center;
}

.buttons-container.buttons-fade-in {
	opacity: 1;
	transform: translateX(-50%) translateY(0);
}

.login-button,
.signup-button {
	width: 100%;
	height: 50px;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: all 0.3s ease;
	display: flex;
	align-items: center;
	justify-content: center;
}

.login-button {
	background-color: #4b3d34;
}

.login-button:hover {
	background-color: #594d44;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(75, 61, 52, 0.3);
}

.signup-button {
	background-color: #b0a695;
}

.signup-button:hover {
	background-color: #9f9485;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(176, 166, 149, 0.3);
}

.button-text {
	color: #ffffff;
	font-family: "Inter", sans-serif;
	font-weight: 600;
	font-size: 16px;
	line-height: 19.36px;
	letter-spacing: 0;
}

/* Responsive Design */
@media (max-width: 440px) {
	.entry-page-container {
		width: 100vw;
		height: 100vh;
	}

	.logo-container {
		width: 300px;
	}

	.buttons-container {
		width: 300px;
	}
}

@media (min-width: 441px) {
	.entry-page-container {
		width: 440px;
		margin: 0 auto;
	}
}
</style>
