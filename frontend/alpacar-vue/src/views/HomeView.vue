<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goToSignupLogin = () => {
  router.push('/signup-login')
}
</script>

<template>
  <main>
    <TheWelcome />
    <div class="navigation">
      <button @click="goToSignupLogin" class="nav-button">
        회원가입/로그인 페이지로 이동
      </button>
    </div>
  </main>
</template>

<style scoped>
.navigation {
  margin-top: 20px;
  text-align: center;
}

.nav-button {
  background-color: #776b5d;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: background-color 0.3s ease;
}

.nav-button:hover {
  background-color: #6a5f52;
}
</style>
