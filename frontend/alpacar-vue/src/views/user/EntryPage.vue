<template>
  <div class="signup-login-container">
    <!-- Main Content -->
    <div class="main-content">
      <!-- Background Image -->
      <div class="background-image"></div>
      
      <!-- Logo Image -->
      <div class="logo-container">
        <div class="logo-image"></div>
      </div>

      <!-- Buttons Container -->
      <div class="buttons-container">
        <button class="login-button" @click="goToLogin">
          <span class="button-text">로그인</span>
        </button>
        <button class="signup-button" @click="goToSignup">
          <span class="button-text">회원가입</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { useRouter } from "vue-router";

export default defineComponent({
  name: "SignupLogin",
  setup() {
    const router = useRouter();

    const goToLogin = () => {
      router.push('/login');
    };

    const goToSignup = () => {
      router.push('/signup');
    };

    return {
      goToLogin,
      goToSignup,
    };
  },
});
</script>

<style scoped>
.signup-login-container {
  width: 100%;
  min-height: 100vh;
  background-color: #f3eeea;
  position: relative;
  overflow-x: hidden;
  font-family: 'Inter', sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.main-content {
  width: 100%;
  max-width: 440px;
  min-height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.background-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('@/assets/background-banner.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

/* Logo Container */
.logo-container {
  position: absolute;
  top: 113px;
  left: 50%;
  transform: translateX(-50%);
  width: 380px;
  height: 59px;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 5;
}

.logo-image {
  width: 100%;
  height: 100%;
  background-image: url('@/assets/alpaca-logo.png');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: 8px;
}

/* Buttons Container */
.buttons-container {
  position: absolute;
  bottom: 150px;
  left: 50%;
  transform: translateX(-50%);
  width: 344px;
  display: flex;
  flex-direction: column;
  gap: 40px;
  z-index: 5;
}

.login-button, .signup-button {
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
  background-color: #776b5d;
}

.login-button:hover {
  background-color: #665a4d;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
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
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 16px;
  line-height: 19.36px;
  letter-spacing: 0;
}

/* Responsive Design */
@media (max-width: 440px) {
  .signup-login-container {
    width: 100vw;
  }
  
  .logo-container {
    width: 300px;
  }
  
  .buttons-container {
    width: 300px;
  }
}

@media (min-width: 441px) {
  .signup-login-container {
    width: 440px;
    margin: 0 auto;
  }
}
</style> 