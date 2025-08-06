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

				<button class="login-button" @click="handleLogin">
					<span>로그인</span>
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

		const handleLogin = async () => {
			if (!adminId.value || !adminPassword.value) {
				return alert("이메일과 비밀번호를 모두 입력해주세요.");
			}
			try {
				// 예: userStore.adminLogin 액션이 있는 경우
				await userStore.adminLogin(adminId.value, adminPassword.value);

				// 로그인 후 관리자 메인 페이지로 이동
				router.push("/admin-main");
			} catch (err: any) {
				console.error("관리자 로그인 실패:", err);
				alert("관리자 로그인 실패: " + (err.message || "알 수 없는 오류"));
			}
		};

		return {
			adminId,
			adminPassword,
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
}

.login-button:hover {
	background-color: #5f554a;
}
</style>
