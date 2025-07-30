<template>
  <div class="forgot-password-container">
    <!-- Main Content -->
    <div class="main-content">
      <!-- Title Section -->
      <div class="title-section">
        <h1 class="forgot-password-title">비밀번호 찾기</h1>
      </div>

      <!-- Forgot Password Form -->
      <div class="forgot-password-form">
        <!-- Name Field -->
        <div class="field-group">
          <label class="field-label">이름</label>
          <input 
            type="text" 
            placeholder="이름 입력" 
            v-model="formData.name"
            class="input-field"
          />
        </div>

        <!-- Email Field -->
        <div class="field-group">
          <label class="field-label">이메일</label>
          <input 
            type="email" 
            placeholder="이메일 입력" 
            v-model="formData.email"
            class="input-field"
          />
        </div>

        <!-- Send Verification Button -->
        <button class="send-verification-button" @click="handleSendVerification">
          <span class="button-text">인증번호 발송</span>
        </button>

        <!-- Verification Code Field -->
        <div class="field-group">
          <label class="field-label">인증번호 입력</label>
          <div class="input-with-button">
            <input 
              type="text" 
              placeholder="인증번호 입력" 
              v-model="formData.verificationCode"
              class="input-field"
            />
            <button class="verify-button">확인</button>
          </div>
        </div>

        <!-- New Password Field -->
        <div class="field-group">
          <label class="field-label">새 비밀번호 입력</label>
          <input 
            type="password" 
            placeholder="비밀번호 입력" 
            v-model="formData.newPassword"
            class="input-field"
          />
          <p class="field-help">영문, 숫자, 특수문자 조합 8-20자리</p>
        </div>

        <!-- New Password Confirm Field -->
        <div class="field-group">
          <label class="field-label">새 비밀번호 확인</label>
          <input 
            type="password" 
            placeholder="비밀번호 입력" 
            v-model="formData.newPasswordConfirm"
            class="input-field"
          />
          <p class="field-help">위와 동일한 비밀번호를 다시 입력해주세요</p>
        </div>

        <!-- Change Password Button -->
        <button class="change-password-button" @click="handleChangePassword">
          <span class="button-text">비밀번호 변경 완료</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive } from "vue";
import { useRouter } from "vue-router";

export default defineComponent({
  name: "ForgotPassword",
  setup() {
    const router = useRouter();
    
    const formData = reactive({
      name: "",
      email: "",
      verificationCode: "",
      newPassword: "",
      newPasswordConfirm: ""
    });

    const handleSendVerification = () => {
      // 인증번호 발송 로직
      console.log("인증번호 발송:", { name: formData.name, email: formData.email });
    };

    const handleChangePassword = () => {
      // 비밀번호 변경 로직
      console.log("비밀번호 변경 시도:", formData);
    };

    return {
      formData,
      handleSendVerification,
      handleChangePassword,
    };
  },
});
</script>

<style scoped>
.forgot-password-container {
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

.verify-button {
  height: 30px;
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

/* Buttons */
.send-verification-button,
.change-password-button {
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
}

.send-verification-button:hover,
.change-password-button:hover {
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