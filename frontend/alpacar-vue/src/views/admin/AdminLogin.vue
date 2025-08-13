<template>
	<div class="admin-login">
		<AdminNavbar :showLogout="false" />
		<div class="login-wrapper">
			<img class="logo" alt="Logo" src="@/assets/alpaca-logo.png" />
			<div class="login-box">
				<div class="title">관리자 로그인</div>

				<div class="input-box">
					<input type="email" placeholder="관리자 이메일 입력" v-model="adminId" @keyup.enter="handleLogin" />
				</div>

				<div class="input-box">
					<input type="password" placeholder="비밀번호 입력" v-model="adminPassword" @keyup.enter="handleLogin" />
				</div>

				<button class="login-button" @click="handleLogin" :disabled="isLoading">
					<span v-if="!isLoading">로그인</span>
					<span v-else class="loading">로그인 중...</span>
				</button>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { defineComponent, ref } from "vue";
import { useRouter } from "vue-router";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";
import { useUserStore } from "@/stores/user";

export default defineComponent({
	name: "AdminLogin",
	components: { AdminNavbar },
	setup() {
		const router = useRouter();
		const userStore = useUserStore();

		const adminId = ref("");
		const adminPassword = ref("");
		const isLoading = ref(false);

		const handleLogin = async () => {
			if (isLoading.value) return;
			if (!adminId.value || !adminPassword.value) {
				return alert("이메일과 비밀번호를 모두 입력해주세요.");
			}
			
			isLoading.value = true;
			try {
				// 관리자 로그인 시도
				console.log("[ADMIN LOGIN] 로그인 시도 중...");
				await userStore.adminLogin(adminId.value, adminPassword.value);
				
				// 로그인 성공 후 사용자 정보 확인
				console.log("[ADMIN LOGIN] 로그인 성공. 사용자 정보:", userStore.me);
				console.log("[ADMIN LOGIN] 관리자 여부:", userStore.me?.is_staff);

				// 로그인 후 관리자 메인 페이지로 이동
				console.log("[ADMIN LOGIN] 관리자 메인 페이지로 이동");
				router.push("/admin-main");
			} catch (err: any) {
				console.error("관리자 로그인 실패:", err);
				alert("관리자 로그인 실패: " + (err.message || "알 수 없는 오류"));
			} finally {
				isLoading.value = false;
			}
		};

		return {
			adminId,
			adminPassword,
			isLoading,
			handleLogin,
		};
	},
});
</script>

<style scoped>
.admin-login {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
	background-color: #f3eeea;
}

.login-wrapper {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 16px;
}

.logo {
	width: 240px;
	max-width: 60%;
	margin-bottom: 32px;
	object-fit: contain;
}

.login-box {
	background-color: #faf8f5;
	padding: 32px 24px;
	border-radius: 8px;
	box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
	width: 100%;
	max-width: 400px;
	display: flex;
	flex-direction: column;
	gap: 20px;
}

.title {
	font-size: 24px;
	font-weight: 600;
	text-align: center;
	color: #000000;
}

.input-box {
	width: 100%;
}

.input-box input {
	width: 100%;
	padding: 12px 16px;
	font-size: 16px;
	border: 1px solid #cccccc;
	border-radius: 4px;
	background-color: #ffffff;
	box-sizing: border-box;
}

.login-button {
	background-color: #776b5d;
	color: white;
	text-align: center;
	padding: 12px;
	border-radius: 4px;
	font-weight: 600;
	cursor: pointer;
	transition: background-color 0.2s;
	border: none;
}

.login-button:disabled {
	background-color: #999999;
	cursor: not-allowed;
}

.login-button:hover:not(:disabled) {
	background-color: #5f554a;
}

.loading {
	position: relative;
}

.loading::after {
	content: "";
	position: absolute;
	right: -25px;
	top: 50%;
	transform: translateY(-50%);
	width: 16px;
	height: 16px;
	border: 2px solid transparent;
	border-top: 2px solid #ffffff;
	border-radius: 50%;
	animation: spin 1s linear infinite;
}

@keyframes spin {
	from { transform: translateY(-50%) rotate(0deg); }
	to { transform: translateY(-50%) rotate(360deg); }
}
</style>
