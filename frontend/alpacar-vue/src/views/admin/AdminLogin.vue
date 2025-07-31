<template>
  <div class="admin-login">
    <AdminNavbar :showLogout="false" />
    <div class="login-wrapper">
      <img class="logo" alt="Logo" src="@/assets/alpaca-logo.png" />
      <div class="login-box">
        <div class="title">관리자 로그인</div>

        <div class="input-box">
          <input type="text" placeholder="아이디 입력" />
        </div>

        <div class="input-box">
          <input type="password" placeholder="비밀번호 입력" />
        </div>

        <div class="login-button">
          <span>로그인</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import AdminNavbar from '@/views/admin/AdminNavbar.vue';

export default defineComponent({
  name: "AdminLogin",
  components: {
    AdminNavbar,
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
