<template>
  <div class="user-setting">
    <!-- Header -->
    <Header />

    <!-- Back to UserProfile -->
    <button
      class="back-link"
      type="button"
      @click="goToUserProfile"
      aria-label="프로필로 돌아가기"
    >
      <svg viewBox="0 0 24 24" class="back-link__icon" aria-hidden="true">
        <path d="M15 18l-6-6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span class="back-link__text">돌아가기</span>
    </button>

    <!-- Content -->
    <div class="user-setting__content">
      <!-- 프로필 섹션: 전화번호 / 비밀번호 (행 + 우측 꺾쇠) -->
      <div class="profile-card">
        <!-- 전화번호 행 -->
        <button
          class="setting-row"
          type="button"
          @click="openPhoneModal"
        >
          <div class="setting-row__text">
            <div class="setting-row__label">
              전화번호
            </div>
            <div class="setting-row__value">
              {{ isLoadingUserInfo ? '로딩 중...' : (formatPhoneNumber(userInfo?.phone) || '-') }}
            </div>
          </div>
          <span class="chevron" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </button>

        <div class="divider"></div>

        <!-- 비밀번호 행 -->
        <button
          class="setting-row"
          type="button"
          @click="openPasswordModal"
        >
          <div class="setting-row__text">
            <div class="setting-row__label">
              비밀번호
            </div>
            <div class="setting-row__value setting-row__value--placeholder">
              변경하기
            </div>
          </div>
          <span class="chevron" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </button>
      </div>
    </div>

    <!-- Bottom Navigation -->
    <BottomNavigation />

    <!-- 전화번호 변경 모달 -->
    <div
      v-if="showPhoneModal"
      class="modal-overlay"
      @click="closePhoneModal"
    >
      <div
        class="modal modal--phone"
        @click.stop
      >
        <h3 class="modal__title">
          새 전화번호 입력
        </h3>

        <form
          autocomplete="off"
          @submit.prevent
        >
          <!-- 브라우저 자동완성 방해용 더미 -->
          <input type="text" style="display:none" />
          <input type="password" style="display:none" />
          <input type="email" style="display:none" />

          <div class="modal__input-field">
            <input
              :id="'phone-' + uniqueId"
              v-model="phoneDisplay"
              @input="handlePhoneInput"
              @keypress="preventInvalidPhoneChars"
              @focus="onPhoneFocus"
              type="text"
              :placeholder="phonePlaceholder"
              class="modal__input"
              maxlength="13"
              autocomplete="off"
              autocorrect="off"
              autocapitalize="off"
              spellcheck="false"
              :name="'phone-field-' + uniqueId"
              inputmode="numeric"
              data-form-type="other"
              data-lpignore="true"
              readonly
              onfocus="this.removeAttribute('readonly');"
            />
          </div>
        </form>

        <div
          v-if="newPhoneNumber && !isPhoneValid"
          class="error-message"
        >
          올바른 전화번호 형식으로 입력해주세요 (숫자 11자리)
        </div>

        <button
          class="modal__button"
          @click="requestPhoneChange"
        >
          변경하기
        </button>
      </div>
    </div>

    <!-- 비밀번호 변경 모달 -->
    <div
      v-if="showPasswordModal"
      class="modal-overlay"
      @click="showPasswordModal = false"
    >
      <div
        class="modal modal--password"
        @click.stop
      >
        <h3 class="modal__title">
          비밀번호 변경
        </h3>

        <div class="section-subtitle">
          현재 비밀번호 입력
        </div>
        <div class="modal__input-field">
          <input
            v-model="currentPassword"
            type="password"
            placeholder="현재 비밀번호를 입력하세요"
            class="modal__input"
            maxlength="20"
          />
        </div>

        <div class="section-subtitle">
          새 비밀번호 입력
        </div>
        <div class="modal__input-field">
          <input
            v-model="newPassword"
            type="password"
            placeholder="새 비밀번호를 입력하세요"
            class="modal__input"
            maxlength="20"
          />
        </div>

        <ul
          v-if="newPassword && !isPasswordValid"
          class="password-rules"
        >
          <li :class="passwordLengthValid ? 'valid' : 'invalid'">8~20자</li>
          <li :class="passwordLetterValid ? 'valid' : 'invalid'">문자 포함</li>
          <li :class="passwordNumberValid ? 'valid' : 'invalid'">숫자 포함</li>
          <li :class="passwordSpecialValid ? 'valid' : 'invalid'">특수문자 포함</li>
          <li :class="passwordNoTripleValid ? 'valid' : 'invalid'">동일문자 3연속 불가</li>
          <li :class="passwordNoSeqValid ? 'valid' : 'invalid'">연속문자 3연속 불가</li>
        </ul>

        <div class="section-subtitle">
          새 비밀번호 확인
        </div>
        <div class="modal__input-field">
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="새 비밀번호를 다시 입력하세요"
            class="modal__input"
            maxlength="20"
          />
        </div>

        <div
          v-if="confirmPassword && !isPasswordConfirmValid"
          class="error-message"
        >
          비밀번호가 일치하지 않습니다
        </div>

        <button
          class="modal__button"
          @click="requestPasswordChange"
        >
          변경하기
        </button>
      </div>
    </div>

    <!-- 이메일 인증(전화/비번 공용) -->
    <div
      v-if="showEmailVerificationModal"
      class="modal-overlay"
      @click="showEmailVerificationModal = false"
    >
      <div
        class="modal modal--email-verify"
        @click.stop
      >
        <h3 class="modal__title">
          {{ verificationTarget === 'phone' ? '전화번호 변경' : '비밀번호 변경' }} 인증
        </h3>

        <div class="email-info">
          <span>{{ isLoadingUserInfo ? '로딩 중...' : userInfo?.email }}로 인증번호를 발송합니다.</span>
        </div>

        <div class="verification-step">
          <button
            class="modal__button"
            @click="sendEmailVerification"
            :disabled="emailSent"
          >
            {{ emailSent ? '인증번호 발송됨' : '인증번호 발송' }}
          </button>
        </div>

        <div
          v-if="emailSent"
          class="verification-input"
        >
          <div class="modal__input-field">
            <input
              v-model="verificationCode"
              type="text"
              placeholder="인증번호를 입력하세요"
              class="modal__input"
              maxlength="6"
            />
          </div>

          <button
            class="modal__button"
            @click="verifyEmailCode"
            :disabled="!verificationCode || emailVerified"
          >
            {{ emailVerified ? '인증완료' : '인증확인' }}
          </button>
        </div>

        <div
          v-if="emailVerified"
          class="verification-complete"
        >
          <button
            class="modal__button modal__button--success"
            @click="verificationTarget === 'phone' ? executePhoneChange() : confirmPasswordChange()"
          >
            {{ verificationTarget === 'phone' ? '전화번호 변경' : '비밀번호 변경' }} 완료
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { BACKEND_BASE_URL } from "@/utils/api";
import { apiClient } from "@/api/parking";

/* ====== 스토어 ====== */
const router = useRouter();
const userStore = useUserStore();

// 동적으로 로딩되는 사용자 상세 정보 (민감정보 포함)
const detailedUserInfo = ref<any>(null);
const isLoadingUserInfo = ref(false);

// 로컬 스토리지의 기본 사용자 정보 (민감정보 제외)
const userInfo = computed(() => detailedUserInfo.value || userStore.me);

// 민감한 사용자 정보 동적 로딩
const loadDetailedUserInfo = async () => {
  if (isLoadingUserInfo.value) return;
  
  try {
    isLoadingUserInfo.value = true;
    const userData = await userStore.fetchDetailedUserInfo();
    detailedUserInfo.value = userData;
    console.log('[UserSetting] 사용자 상세 정보 로딩 완료');
  } catch (error) {
    console.error('[UserSetting] 사용자 정보 로딩 실패:', error);
    alert('사용자 정보를 불러오는데 실패했습니다.');
  } finally {
    isLoadingUserInfo.value = false;
  }
};

const goToUserProfile = () => {
  router.push('/user-profile'); // 또는 router.back();
};

// 소셜 로그인 유저 여부 확인 (보안 검증용)
const isSocialUser = computed(() => {
  return userInfo.value?.is_social_user || false;
});

// const getAccessToken = () =>
//   localStorage.getItem("access_token") ||
//   sessionStorage.getItem("access_token") ||
//   localStorage.getItem("access") ||
//   sessionStorage.getItem("access");

/* ====== 행(꺾쇠) 클릭 핸들러 ====== */
const openPhoneModal = () => {
  showPhoneModal.value = true;
  // 입력창 자동완성 방지용 readonly 제거 타이밍 보정
  setTimeout(() => {
    const el = document.querySelector(`#phone-${uniqueId.value}`) as HTMLInputElement | null;
    if (el) el.removeAttribute("readonly");
  }, 100);
};
const closePhoneModal = () => {
  showPhoneModal.value = false;
};
const openPasswordModal = () => {
  showPasswordModal.value = true;
};

/* ====== 전화번호 ====== */
const phonePlaceholder = ref("ex) 010-1234-5678");
const uniqueId = ref(Date.now());
const phoneDisplay = ref("");
const newPhoneNumber = ref("");
const showPhoneModal = ref(false);

const isPhoneValid = computed(() => /^[0-9]{11}$/.test(newPhoneNumber.value));

const handlePhoneInput = (e: Event) => {
  let digits = (e.target as HTMLInputElement).value.replace(/[^0-9]/g, "");
  if (digits.length > 11) digits = digits.slice(0, 11);
  const p1 = digits.slice(0, 3);
  const p2 = digits.length >= 4 ? digits.slice(3, 7) : "";
  const p3 = digits.length >= 8 ? digits.slice(7) : "";
  phoneDisplay.value = [p1, p2, p3].filter(Boolean).join("-");
  newPhoneNumber.value = digits;
};
const preventInvalidPhoneChars = (e: KeyboardEvent) => {
  const char = e.key;
  if (!/[0-9]/.test(char) && !["Backspace","Delete","ArrowLeft","ArrowRight","Tab"].includes(char)) e.preventDefault();
};
const onPhoneFocus = (e: FocusEvent) => {
  const target = e.target as HTMLInputElement;
  if (target.hasAttribute("readonly")) target.removeAttribute("readonly");
  target.setAttribute("autocomplete","off");
  uniqueId.value = Date.now();
};

const showEmailVerificationModal = ref(false);
const emailSent = ref(false);
const emailVerified = ref(false);
const verificationCode = ref("");
const verificationTarget = ref<'phone' | 'password'>('phone');

const requestPhoneChange = async () => {
  if (!newPhoneNumber.value.trim()) {
    alert("새 전화번호를 입력해주세요.");
    return;
  }
  
  // 사용자 정보가 로딩되지 않았으면 로딩
  if (!detailedUserInfo.value) {
    await loadDetailedUserInfo();
  }
  
  if (!userInfo.value?.email) {
    alert("이메일 정보를 불러오는데 실패했습니다.");
    return;
  }
  
  verificationTarget.value = "phone";
  emailSent.value = false;
  emailVerified.value = false;
  verificationCode.value = "";
  showEmailVerificationModal.value = true;
};

const executePhoneChange = async () => {
  if (!emailVerified.value) { alert("이메일 인증을 먼저 완료해주세요."); return; }
  if (!newPhoneNumber.value || !isPhoneValid.value) { alert("올바른 전화번호를 입력해주세요."); return; }

  const payload = {
    phone: newPhoneNumber.value,
    nickname: userInfo.value?.nickname ?? "",
    name: userInfo.value?.name ?? "",
  };

  try {
    await apiClient.put("/users/me/", payload);   // ← fetch 대신 apiClient 사용
    alert("전화번호가 성공적으로 변경되었습니다.");
    showEmailVerificationModal.value = false;
    showPhoneModal.value = false;
    newPhoneNumber.value = "";
    phoneDisplay.value = "";
    emailSent.value = false;
    emailVerified.value = false;
    verificationCode.value = "";
    await userStore.fetchMe();                    // UI 최신화
  } catch (e: any) {
    if (e?.code === "SESSION_EXPIRED") {
      userStore.clearUser();
      router.push("/login");
      return;
    }
    const msg = e?.response?.data?.detail || e?.response?.data?.message || e?.message || "서버 오류";
    alert("전화번호 변경 실패: " + msg);
  }
};



/* ====== 비밀번호 ====== */
const showPasswordModal = ref(false);
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");

const passwordLengthValid = computed(() => newPassword.value.length >= 8 && newPassword.value.length <= 20);
const passwordLetterValid = computed(() => /[a-zA-Z]/.test(newPassword.value));
const passwordNumberValid = computed(() => /\d/.test(newPassword.value));
const passwordSpecialValid = computed(() => /[$@!%*#?&/]/.test(newPassword.value));
const passwordNoTripleValid = computed(() => !/(\w)\1\1/.test(newPassword.value));
const passwordNoSeqValid = computed(() => {
  for (let i = 0; i < newPassword.value.length - 2; i++) {
    const a = newPassword.value.charCodeAt(i);
    const b = newPassword.value.charCodeAt(i + 1);
    const c = newPassword.value.charCodeAt(i + 2);
    if ((b === a + 1 && c === b + 1) || (b === a - 1 && c === b - 1)) return false;
  }
  return true;
});
const isPasswordValid = computed(() =>
  [passwordLengthValid, passwordLetterValid, passwordNumberValid, passwordSpecialValid, passwordNoTripleValid, passwordNoSeqValid].every(v => v.value)
);
const isPasswordConfirmValid = computed(() => confirmPassword.value === newPassword.value && confirmPassword.value.length > 0);

const requestPasswordChange = async () => {
  // 사용자 정보가 로딩되지 않았으면 로딩
  if (!detailedUserInfo.value) {
    await loadDetailedUserInfo();
  }
  
  if (!userInfo.value?.email) {
    alert("이메일 정보를 불러오는데 실패했습니다.");
    return;
  }
  
  verificationTarget.value = "password";
  emailSent.value = false;
  emailVerified.value = false;
  verificationCode.value = "";
  showEmailVerificationModal.value = true;
};

const confirmPasswordChange = async () => {
  if (!emailVerified.value) { alert("이메일 인증을 먼저 완료해주세요."); return; }
  if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
    return alert("모든 비밀번호 필드를 입력해주세요.");
  }
  if (newPassword.value !== confirmPassword.value) {
    return alert("새 비밀번호가 일치하지 않습니다.");
  }

  try {
    await userStore.changePassword(currentPassword.value, newPassword.value); // 서버 의존(테스트 시 주석 가능)
    alert("비밀번호가 성공적으로 변경되었습니다. (테스트)");
    showEmailVerificationModal.value = false;
    showPasswordModal.value = false;
  } catch (e: any) {
    console.error(e);
    alert("변경 실패: " + e.message);
  } finally {
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  }
};

/* ====== 이메일 인증 공통 ====== */
const sendEmailVerification = async () => {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/request/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
        // "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ email: userInfo.value?.email })
    });
    if (response.ok) {
      emailSent.value = true;
      alert("인증번호를 발송했습니다. (테스트)");
    } else {
      alert("인증번호 발송 실패");
    }
  } catch {
    alert("인증번호 발송 실패 (테스트 모드)");
  }
};

const verifyEmailCode = async () => {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/verify/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: userInfo.value?.email, code: verificationCode.value })
    });
    if (response.ok) {
      emailVerified.value = true;
      alert("이메일 인증이 완료되었습니다. (테스트)");
    } else {
      const error = await response.json();
      alert(error.detail || "인증 실패");
    }
  } catch {
    alert("인증 실패 (테스트 모드)");
  }
};

/* ====== 보안 검증 ====== */
const checkAuthenticationStatus = () => {
  // 1. 소셜 로그인 유저인 경우 접근 차단
  if (isSocialUser.value) {
    alert('소셜 로그인 사용자는 이 페이지에 접근할 수 없습니다.');
    router.push('/user-profile');
    return false;
  }
  // 2. 남아있는 일회용 토큰 정리
  const remainingToken = sessionStorage.getItem('user-setting-one-time-auth');
  if (remainingToken) {
    sessionStorage.removeItem('user-setting-one-time-auth');
    console.log('[UserSetting] 남은 일회용 토큰 삭제');
  }
  // 3. 정상 접근
  console.log('[UserSetting] 정상적인 인증 절차를 통한 접근');
  return true;
};

/* ====== 마운트(테스트용) ====== */
onMounted(async () => {
  if (!checkAuthenticationStatus()) return;

  // 사용자 상세 정보 로딩
  await loadDetailedUserInfo();

  const cleanupTokens = () => {
    sessionStorage.removeItem('user-setting-one-time-auth');
    console.log('[UserSetting] 페이지 이탈 시 토큰 정리');
  };

  window.addEventListener('beforeunload', cleanupTokens);
  window.addEventListener('pagehide', cleanupTokens);

  // 컴포넌트 언마운트 시 정리
  return () => {
    window.removeEventListener('beforeunload', cleanupTokens);
    window.removeEventListener('pagehide', cleanupTokens);
    cleanupTokens();
  };
});

/* ====== 유틸 ====== */
const formatPhoneNumber = (phone: string | undefined | null) => {
  if (!phone) return null;
  const digits = phone.replace(/\D/g, "");
  if (digits.length !== 11) return phone;
  return digits.replace(/(\d{3})(\d{4})(\d{4})/, "$1-$2-$3");
};
</script>

<style scoped>
/* ── 전체 레이아웃 ── */
.user-setting {
  width: 440px;
  height: 956px;
  position: relative;
  background: #f3edea;
  overflow: hidden;
  margin: 0 auto;
}

.user-setting__content {
  position: relative;
  padding-top: 40px;
  height: calc(100% - 160px);
  overflow-y: auto;
  padding-left: 20px;
  padding-right: 20px;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 80px 0px 0 20px; /* 상단 여백만 주어 Header와 간격 확보 */
  background: transparent;
  border: none;
  cursor: pointer;
  color: #776b5d;
  font-size: 14px;
  font-weight: 700;
}
.back-link:hover { opacity: 0.85; }
.back-link__icon { width: 20px; height: 20px; }
.back-link__text { line-height: 1; }

/* ── 프로필 카드(행 리스트) ── */
.profile-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(119, 107, 93, 0.1);
}

.setting-row {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 16px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
}

.setting-row:hover {
  background: rgba(119, 107, 93, 0.04);
}

.setting-row__text {
  flex: 1 1 auto;
  min-width: 0;
}

.setting-row__label {
  font-size: 18px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 4px;
}

.setting-row__value {
  font-size: 15px;
  color: #7a7a7a;
  word-break: break-all;
}

.setting-row__value--placeholder {
  color: #9a9a9a;
}

.chevron {
  flex: 0 0 24px;
  width: 24px;
  height: 24px;
  color: #8a837a;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.chevron svg {
  width: 20px;
  height: 20px;
}

.divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.08);
  margin-left: 16px;
  margin-right: 16px;
}

/* ── 모달 공통 ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #f3eeea;
  width: 90%;
  max-width: 360px;
  padding: 27px 24px 32px;
  border-radius: 10px;
}

.modal__title {
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 20px;
}

.modal__input-field {
  width: 100%;
  background: #ffffff;
  border: 1px solid #ccc;
  margin-bottom: 16px;
  padding: 10px 12px;
  box-sizing: border-box;
  border-radius: 8px;
}

.modal__input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 16px;
  padding: 0;
  box-sizing: border-box;
  background: transparent
}

.modal__button {
  width: 100%;
  height: 48px;
  background: #776b5d;
  color: #ffffff;
  border: none;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.modal__button--success {
  background: #4caf50;
}

/* 비밀번호 유효성 안내 */
.password-rules {
  list-style: none;
  padding: 0;
  margin: 5px 0 15px 0;
  font-size: 12px;
}

.password-rules li {
  padding: 2px 0;
  color: #999999;
}

.password-rules li.valid {
  color: #4caf50;
}

.password-rules li.valid::before {
  content: "✓ ";
}

.password-rules li.invalid {
  color: #f44336;
}

.password-rules li.invalid::before {
  content: "✗ ";
}

/* 메시지 */
.error-message {
  color: #f44336;
  font-size: 14px;
  margin-bottom: 12px;
}

.email-info {
  text-align: center;
  margin-bottom: 16px;
  font-size: 14px;
  color: #666666;
}

.verification-step {
  margin-bottom: 16px;
}

.verification-input {
  margin-bottom: 16px;
}

.verification-complete {
  margin-top: 10px;
}

/* Responsive */
@media (max-width: 440px) {
  .user-setting {
    width: 100vw;
    height: 100vh;
  }

  .user-setting__content {
    padding-left: 15px;
    padding-right: 15px;
  }

  .setting-row__label {
    font-size: 17px;
  }

  .setting-row__value {
    font-size: 14px;
  }
}

@media (min-width: 441px) {
  .user-setting {
    width: 440px;
    height: auto;
    min-height: 100vh;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
  }

  .user-setting__content {
    flex: 1;
    height: auto;
    min-height: calc(100vh - 160px);
    padding-bottom: 20px;
  }
}
</style>
