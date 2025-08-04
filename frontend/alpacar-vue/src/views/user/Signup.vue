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
            v-model="formData.name"
            class="input-field"
          />
          <p class="field-help">실명을 입력해주세요</p>
        </div>

        <!-- Email Field -->
        <div class="field-group">
          <label class="field-label">이메일 *</label>
          <div class="input-with-button">
            <input 
              type="email" 
              placeholder="이메일을 입력하세요" 
              v-model="formData.email"
              class="input-field"
            />
            <button class="duplicate-check-button">중복 확인</button>
          </div>
        </div>

        <!-- Password Field -->
        <div class="field-group">
          <label class="field-label">비밀번호 *</label>
          <input 
            type="password" 
            placeholder="비밀번호를 입력하세요" 
            v-model="formData.password"
            class="input-field"
          />
          <p class="field-help">영문, 숫자, 특수문자 조합 8-20자리</p>
        </div>

        <!-- Password Confirm Field -->
        <div class="field-group">
          <label class="field-label">비밀번호 확인 *</label>
          <input 
            type="password" 
            placeholder="비밀번호를 다시 입력하세요" 
            v-model="formData.passwordConfirm"
            class="input-field"
          />
          <p class="field-help">위와 동일한 비밀번호를 다시 입력해주세요</p>
        </div>

        <!-- Phone Field -->
        <div class="field-group">
          <label class="field-label">전화번호 *</label>
          <input 
            type="tel" 
            placeholder="전화번호를 입력하세요" 
            v-model="formData.phone"
            class="input-field"
          />
        </div>

        <!-- Nickname Field -->
        <div class="field-group">
          <label class="field-label">닉네임 *</label>
          <div class="input-with-button">
            <input 
              type="text" 
              placeholder="닉네임을 입력하세요" 
              v-model="formData.nickname"
              class="input-field"
            />
            <button class="duplicate-check-button">중복 확인</button>
          </div>
        </div>

        <!-- Signup Button -->
        <button class="signup-button" @click="handleSignup">
          <router-link to="/social-login-info" class="link">
            <span class="button-text">회원가입</span>
          </router-link>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive } from "vue";
import { useRouter } from "vue-router";

export default defineComponent({
  name: "Signup",
  setup() {
    const router = useRouter();
    
    const formData = reactive({
      name: "",
      email: "",
      password: "",
      passwordConfirm: "",
      phone: "",
      nickname: "",
    });

    const goBack = () => {
      router.go(-1);
    };

    const handleComplete = () => {
      // 완료 버튼 로직
      console.log("완료 버튼 클릭");
    };

    const handleSignup = () => {
      // 회원가입 로직
      console.log("회원가입 시도:", formData);
    };

    return {
      formData,
      goBack,
      handleComplete,
      handleSignup,
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
  font-family: 'Inter', sans-serif;
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

/* Signup Button */
.signup-button {
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
  margin-top: 20px;
}

.signup-button:hover {
  background-color: #665a4d;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
}

.button-text {
  color: #ffffff;
  font-family: 'Inter', sans-serif;
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